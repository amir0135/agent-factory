#!/usr/bin/env bash
# Create or update the user's one Factory Project. Optional argument: owner/repo.
set -euo pipefail

TOKEN=${FACTORY_PROJECT_TOKEN:-}
if [ -z "$TOKEN" ] && command -v security >/dev/null; then
  TOKEN=$(security find-generic-password -a "$USER" -s agent-factory-project-pat -w 2>/dev/null || true)
fi
if [ -z "$TOKEN" ]; then
  echo "Set FACTORY_PROJECT_TOKEN (classic PAT with project + repo scopes), or store it as agent-factory-project-pat in Keychain." >&2
  exit 1
fi
export GH_TOKEN="$TOKEN"
OWNER=$(gh api user --jq .login)
REPO=${1:-}
if [ -n "$REPO" ] && [[ "$REPO" != "$OWNER/"* ]]; then
  echo "Expected a repository owned by $OWNER: $REPO" >&2
  exit 1
fi

gql() {
  local query=$1 variables=${2:-'{}'}
  jq -nc --arg q "$query" --argjson v "$variables" '{query:$q,variables:$v}' |
    gh api graphql --input -
}
project_query='query($owner:String!){user(login:$owner){id projectsV2(first:100){nodes{id number title url readme fields(first:100){nodes{... on ProjectV2SingleSelectField{id name options{id name color description}} ... on ProjectV2Field{id name}}}}}}}'
data=$(gql "$project_query" "$(jq -nc --arg owner "$OWNER" '{owner:$owner}')")
owner_id=$(jq -r '.data.user.id' <<<"$data")
project=$(jq -c '.data.user.projectsV2.nodes[] | select(.title == "🏭 Factory")' <<<"$data" | head -n 1)
if [ -z "$project" ]; then
  data=$(gql 'mutation($owner:ID!){createProjectV2(input:{ownerId:$owner,title:"🏭 Factory"}){projectV2{id number title url readme fields(first:100){nodes{... on ProjectV2SingleSelectField{id name options{id name color description}} ... on ProjectV2Field{id name}}}}}}}' \
    "$(jq -nc --arg owner "$owner_id" '{owner:$owner}')")
  project=$(jq -c '.data.createProjectV2.projectV2' <<<"$data")
fi
id=$(jq -r .id <<<"$project")
number=$(jq -r .number <<<"$project")
url=$(jq -r .url <<<"$project")

ensure_field() {
  local name=$1 options=$2 field options_json
  field=$(jq -c --arg name "$name" '.fields.nodes[] | select(.name == $name)' <<<"$project" | head -n 1)
  if [ -z "$field" ]; then
    gql 'mutation($p:ID!,$name:String!,$options:[ProjectV2SingleSelectFieldOptionInput!]!){createProjectV2Field(input:{projectId:$p,name:$name,dataType:SINGLE_SELECT,singleSelectOptions:$options}){projectV2Field{... on ProjectV2SingleSelectField{id}}}}' \
      "$(jq -nc --arg p "$id" --arg name "$name" --argjson options "$options" '{p:$p,name:$name,options:$options}')" >/dev/null
  else
    # Preserve existing option IDs and append only missing names.
    options_json=$(jq -c --argjson desired "$options" '
      [.options[] | {id,name,color,description}] as $old |
      $old + [$desired[] | select(.name as $n | [$old[].name] | index($n) | not)]' <<<"$field")
    if [ "$(jq length <<<"$options_json")" -ne "$(jq '.options | length' <<<"$field")" ] ||
       [ "$name" = Status ] && [ "$(jq -c '[.options[].name]' <<<"$field")" != "$(jq -c '[.[].name]' <<<"$options")" ]; then
      if [ "$name" = Status ]; then
        options_json=$(jq -nc --argjson desired "$options" --argjson old "$(jq '.options' <<<"$field")" '
          [$desired[] | . as $d | ($old[] | select(.name == $d.name)) // $d |
            {id,name,color,description} | with_entries(select(.value != null))]')
      fi
      gql 'mutation($field:ID!,$options:[ProjectV2SingleSelectFieldOptionInput!]!){updateProjectV2Field(input:{fieldId:$field,singleSelectOptions:$options}){projectV2Field{... on ProjectV2SingleSelectField{id}}}}' \
        "$(jq -nc --arg field "$(jq -r .id <<<"$field")" --argjson options "$options_json" '{field:$field,options:$options}')" >/dev/null
    fi
  fi
}
status_options=$(jq -nc '["📥 Inbox","🧠 Planning","📋 Ready","🔨 Building","👀 In review","🙋 Needs you","✅ Done"] |
  to_entries | map({name:.value, color:(["GRAY","BLUE","YELLOW","ORANGE","PURPLE","RED","GREEN"][.key]),description:""})')
type_options=$(jq -nc '["Feature","Change","Bug","Task"] | map({name:.,color:"GRAY",description:""})')
ensure_field Status "$status_options"
ensure_field Type "$type_options"
app=${REPO#*/}
[ -n "$REPO" ] || app=agent-factory
app_options=$(jq -nc --arg app "$app" '[{name:$app,color:"BLUE",description:""}]')
ensure_field App "$app_options"

if [ -n "$REPO" ]; then
  repo_id=$(gh api "repos/$REPO" --jq .node_id)
  # Linking is idempotent: GitHub returns the existing link if already linked.
  gql 'mutation($p:ID!,$r:ID!){linkProjectV2ToRepository(input:{projectId:$p,repositoryId:$r}){repository{id}}}' \
    "$(jq -nc --arg p "$id" --arg r "$repo_id" '{p:$p,r:$r}')" >/dev/null
  readme=$(jq -r '.readme // ""' <<<"$project")
  link="[$REPO](https://github.com/$REPO/issues?q=is%3Aissue+label%3Astatus)"
  if [[ "$readme" != *"$link"* ]]; then
    readme="${readme:+$readme$'\n'}- $link — pinned 📊 Status issue"
    gql 'mutation($p:ID!,$readme:String!){updateProjectV2(input:{projectId:$p,readme:$readme}){projectV2{id}}}' \
      "$(jq -nc --arg p "$id" --arg readme "$readme" '{p:$p,readme:$readme}')" >/dev/null
  fi
  gh variable set FACTORY_PROJECT_NUMBER -R "$REPO" --body "$number"
fi
echo "Factory board: $url"
echo "GitHub Projects API cannot create or configure views. In $url: (1) click + New view > Board and group by Status; (2) + New view > Table, name it By app, group by App; (3) + New view > Table, name it Needs you, filter Status:\"🙋 Needs you\"."

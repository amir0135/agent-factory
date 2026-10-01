# Acceptance scripts

One script per row in `product/ACCEPTANCE_CRITERIA.md`, named `<AC-ID>.sh`, run from the repo root.
Each runs ONLY the tests that prove its row (e.g. `npx vitest run src/auth/bearer.test.ts`) and exits non-zero if the criterion does not hold.
The builder writes the script and its tests in the same PR that flips the row to `done`. A missing script means the row is not done.

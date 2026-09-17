# PR #12 UAT handoff

Integrated main 7e92dcb798e0d18f8617433db99e63336ae5bd0e into PR head 2585f7cb309d050e1e3bf357df880500be09a2d9.

Changes: union of .gitignore exclusions; explicit aborted-signal guard before setResult; unknown-typed error handling with obsolete-request suppression; typed form updates; four React/jsdom regression tests; dedicated carbon frontend/backend CI.

Local evidence on the integrated tree:
- Python full regression: 74 passed (7 dependency/datetime deprecation warnings).
- React component regression: 4 passed (out-of-order results, loading ownership, StrictMode/debounce/unmount, obsolete errors and recovery).
- Frontend TypeScript/Vite build and ESLint: passed.
- Required UAT-module Ruff checks and EF-05 source registry validation: passed.

Before UAT acceptance:
- [ ] Verify both GitHub workflows pass on the final pushed SHA and the PR is mergeable.
- [ ] Reviewer accepts the patch and integration; record the tested SHA.
- [ ] Deploy the accepted SHA to private UAT with the correct VITE_API_URL.
- [ ] Browser smoke test health/calculation, rapid edits, delayed responses, API failure/recovery, and navigation away during a request.
- [ ] Record UAT evidence and approval before production release.

React/jsdom tests are component tests, not deployed browser tests. These checks do not certify ESG/legal claims, mock integrations, tenant isolation, or production readiness. No production deployment is part of this change.

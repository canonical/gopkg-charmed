.. _ci-workflows:

CI workflows for documentation and tutorial validation
======================================================

Automatic docs checks
---------------------

Workflow: ``.github/workflows/automatic-doc-checks.yml``

Purpose:

- run documentation checks when docs-related files change
- avoid unnecessary CI usage for unrelated code changes

Check removed URLs
------------------

Workflow: ``.github/workflows/check-removed-urls.yml``

Purpose:

- detect removed documentation URLs in pull requests to ``main``
- protect release-path documentation links from accidental breakage

Tutorial integration smoke
--------------------------

Workflow: ``.github/workflows/tutorial-integration-smoke.yml``

Purpose:

- run integration tests when tutorial or deployment docs change
- validate that the documented deploy-and-verify flow remains aligned with
  deployable charm behavior

Where it comes from:

- The workflow file lives in this repository:
  ``.github/workflows/tutorial-integration-smoke.yml``
- The job itself reuses Canonical's shared integration workflow:
  ``canonical/charm-ci/.github/workflows/integration-test.yml`` pinned to a
  specific commit for reproducibility.

Current behavior:

- triggers only on docs tutorial/how-to/reference changes and related
  integration test files
- executes the charm integration test suite through the existing charm-ci
  reusable workflow

Automatic vs manual linkage
---------------------------

The linkage is path-trigger based, not content-aware parsing.

- Automatic part:
  if a pull request changes files matching ``on.pull_request.paths`` in
  ``tutorial-integration-smoke.yml``, the workflow runs automatically.
- Manual part:
  if you move tutorial files to new paths or introduce new docs locations that
  should trigger integration smoke, you must update the ``paths`` list in the
  workflow file.


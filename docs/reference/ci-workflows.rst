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

Current behavior:

- triggers only on docs tutorial/how-to/reference changes and related
  integration test files
- executes the charm integration test suite through the existing charm-ci
  reusable workflow

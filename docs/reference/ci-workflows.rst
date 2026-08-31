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

- execute the tutorial's literal shell commands when the tutorial or its
  deployment inputs change
- validate the complete build, deploy, integrate, configure, and verify flow
  in a provisioned Ubuntu environment

Where it comes from:

- The workflow file lives in this repository:
  ``.github/workflows/tutorial-integration-smoke.yml``
- The job itself reuses Canonical's shared documentation test workflow:
  ``canonical/charm-ci/.github/workflows/doc-test.yml`` pinned to a
  specific commit for reproducibility.

Current behavior:

- triggers on tutorial, Spread task, artifact recipe, provisioning, and
  workflow changes
- uses ``opcli tutorial expand`` to extract commands directly from the RST
- executes the generated shell script through the ``docs-ci`` Spread backend
- provisions MicroK8s and Juju, then builds the rock and charm from source

Automatic vs manual linkage
---------------------------

Command synchronization is content-aware; workflow triggering is path-based.

- Automatic part:
  commands are extracted from the tutorial, so edits to its executable code
  blocks change the tested script without requiring duplicate test changes.
- Manual part:
  if you move tutorial files to new paths or introduce new docs locations that
  should trigger integration smoke, you must update the ``paths`` list in the
  workflow file.


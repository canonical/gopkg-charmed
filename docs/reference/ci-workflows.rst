.. _ci-workflows:

.. meta::
  :description: Reference the GitHub Actions workflows that build, lint, link-check, and execute gopkg-charmed documentation.

CI workflows for documentation validation
=========================================

Automatic doc checks
--------------------

Workflow: ``.github/workflows/automatic-doc-checks.yml``

This workflow runs when documentation-related files change, so unrelated code
changes do not consume documentation CI time. It has two intents: it runs the
documentation checks (build, spelling, style, inclusive language, and links),
and it detects documentation URLs removed by a pull request to ``main``, so
release-path links cannot break by accident.

Documentation tests
-------------------

Workflow: ``.github/workflows/documentation-tests.yml``

This workflow executes the literal shell commands from the tutorial and the
how-to guides on a bare Ubuntu system whenever their content or their
deployment inputs change. It validates the complete environment setup, build,
deploy, integrate, configure, and verify flow using only the commands the
guides themselves contain.

The workflow file lives in this repository and reuses Canonical's shared
documentation test workflow,
``canonical/charm-ci/.github/workflows/doc-test.yml``, pinned to a specific
commit for reproducibility.

Current behavior:

- triggers on tutorial, how-to, Spread task, application source, artifact
  recipe, provisioning, and workflow changes
- uses ``opcli tutorial expand`` to extract commands directly from the RST
- executes the generated shell script through the ``docs-ci`` Spread backend
- starts from a bare system: the guides' own commands install the tools,
  enable MicroK8s, bootstrap Juju, and build the rock and charm from source
- composes guides in prerequisite order; both tests start with the setup
  guide and the tutorial, and the second test continues with the ingress
  and hostname how-to guides against the deployment the tutorial leaves
  behind
- runs a page's clean-up commands, marked by the ``# spread-teardown``
  sentinel, only when that page is last in its chain, so the tutorial test
  destroys what it created and the how-to test keeps the deployment
- starts a fresh login shell at each ``# spread-session-break`` sentinel a
  guide emits, mirroring the reader logging out and back in

Automatic vs manual linkage
---------------------------

Command synchronization is content-aware, but workflow triggering is
path-based. Commands are extracted from the guides at test time, so editing an
executable code block changes the tested script without a duplicate test to
maintain. Moving a documentation file to a new path, however, requires
updating the Spread task inputs and the workflow's ``paths`` list by hand.

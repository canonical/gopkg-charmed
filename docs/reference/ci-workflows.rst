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

It runs on changes to the tutorial, the how-to guides, the Spread tasks, the
application source, the artifact recipes, the provisioning files, and the
workflow itself. It also runs every Saturday at 15:00 UTC on ``main``,
alongside the integration tests, so drift in the tools and images the guides
install is caught between documentation changes.

Each run extracts the commands directly from the RST with ``opcli tutorial
expand`` and executes the generated shell script through the ``docs-ci``
Spread backend, starting from a bare system: the guides' own commands install
the tools, enable MicroK8s, bootstrap Juju, and build the rock and charm from
source.

The guides run in prerequisite order. Both tests start with the setup guide
and the tutorial, and the second test continues into the ingress and hostname
how-to guides against the deployment the tutorial leaves behind. Two sentinels
control the boundaries: a page's clean-up commands, marked by
``# spread-teardown``, run only when that page is last in its chain, so the
tutorial test destroys what it created while the how-to test keeps the
deployment; and each ``# spread-session-break`` a guide emits starts a fresh
login shell, mirroring the reader logging out and back in.

Automatic and manual linkage
----------------------------

Command synchronization is content-aware, but workflow triggering is
path-based. Commands are extracted from the guides at test time, so editing an
executable code block changes the tested script without a duplicate test to
maintain. Moving a documentation file to a new path, however, requires
updating the Spread task inputs and the workflow's ``paths`` list by hand.

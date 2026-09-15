.. _ci-workflows:

.. meta::
  :description: Reference the GitHub Actions workflows that test and publish the gopkg-charmed charm and that build, check, and execute its documentation.

CI workflows
============

Integration tests
-----------------

Workflow: ``.github/workflows/integration-test.yaml``

This workflow builds the rock and the charm, then runs the Juju integration
suite in ``app/charm/tests/integration`` on a fresh MicroK8s cloud. It reuses
Canonical's shared workflow,
``canonical/charm-ci/.github/workflows/integration-test.yml``, pinned to a
specific commit, and runs each test module as its own job.

Current behavior:

- runs on every pull request, on every push to ``main``, and every Saturday
  at 15:00 UTC
- ``test_charm.py`` deploys the charm with the freshly built image and checks
  that one unit becomes active and answers the health check
- ``test_integrations.py`` integrates each of the charm's endpoints with a
  published counterpart and checks that both sides settle in ``active``:
  ``ingress`` with ``nginx-ingress-integrator``, which must then route
  ``gopkg.example.com`` to the service; ``logging`` with ``loki-k8s``;
  ``metrics-endpoint`` with ``prometheus-k8s``, which must register a scrape
  target for the charm; and ``grafana-dashboard`` with ``grafana-k8s``
- the Loki, Prometheus, and Grafana charms come from the ``2/stable``
  channel, which is published for amd64 only, so those tests are skipped on
  arm64 hosts

Charm publication
-----------------

Workflow: ``.github/workflows/publish_charm.yaml``

This workflow publishes the charm and its rock to Charmhub on every push to
``main``. It reuses ``canonical/charm-ci/.github/workflows/publish-artifacts.yml``,
pinned to the same commit as the integration tests.

Current behavior:

- finds the most recent successful integration-test run for the exact source
  tree being published, and downloads the charm and rock that run built and
  tested, so nothing untested is uploaded
- uploads the rock as the ``app-image`` resource and releases the charm to
  the channel declared in ``artifacts.yaml``, ``latest/edge``
- tags the commit with the published revision and creates a GitHub release
  for the run
- can be started by hand from the Actions tab to publish to another channel,
  for example to promote a tested revision to ``latest/stable``, or to
  validate without uploading

If the workflow reports that no successful integration-test run exists for
the tree, the merge commit was not tested yet, which happens when a branch
was squash-merged while behind ``main``. Wait for the push-triggered
integration-test run on ``main`` to pass, then re-run the publication.

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

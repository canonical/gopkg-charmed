.. _improve-code:

Improve the code
================

Use this path for changes to the Go service, charm, rock, or integration tests.
Every code contribution must pass the Go and charm checks and the full
integration suite. The integration suite rebuilds the rock and charm, deploys
them with Juju, and verifies the running service.

Prerequisites
-------------

Complete :ref:`Set up a local Linux environment
<set-up-a-local-linux-environment>` before running the tests on this page. That
guide provides the supported operating system, architectures, tested hardware
allocation, and required tools.

Understand the components
-------------------------

This repository contains three cooperating components:

- The Go service under ``app/`` serves the gopkg.in HTTP endpoints.
- The rock recipe at ``app/rockcraft.yaml`` packages the service as an OCI
  image.
- The charm under ``app/charm/`` configures and operates that image with Juju.

Read :ref:`Juju charms and rocks <juju-charms-and-rocks>` before changing the
rock or charm if these concepts are new to you.

Run all tests
-------------

Run the Go checks from the repository root:

.. code-block:: bash

   cd ~/gopkg-charm/app
   test -z "$(gofmt -l .)"
   go vet ./...
   go build ./...
  go test -race ./...

The formatting command prints nothing when all files are formatted. The test
command reports ``ok`` for passing packages, and the other commands complete
without errors.

Next, run the charm checks:

.. code-block:: bash

   cd ~/gopkg-charm/app/charm
   tox -e lint,unit,static

These environments check formatting and types, run the unit tests, and perform
static security analysis. Tox creates isolated environments under
``app/charm/.tox``.

Finally, return to the repository root and run the full integration suite:

.. code-block:: bash

   cd ~/gopkg-charm
   app/charm/tests/integration/run_full_local_suite.sh

The script verifies its prerequisites, rebuilds and publishes the rock, repacks
the charm, deploys it to a temporary Juju model, and runs the integration tests.
A successful run ends with ``Full local Juju integration suite completed``.

If you need to inspect or repeat individual stages, follow
:ref:`full-integration-suite-local`.

Keep code and documentation aligned
-----------------------------------

Update the documentation when a code change affects configuration, deployment,
commands, supported platforms, or user-visible behavior. Then run both the
relevant code tests above and the checks in :ref:`improve-documentation`.

Before you open a pull request
------------------------------

Confirm that:

- the Go checks pass
- the charm lint, unit, and static checks pass
- the full integration suite repacks and deploys the rock and charm successfully
- user-visible behavior and commands are documented
- generated rocks, charms, virtual environments, and build output are not
  committed
- the pull request's required GitHub checks pass
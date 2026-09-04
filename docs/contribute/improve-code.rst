.. _improve-code:

Improve the code
================

Use this path for changes to the Go service, charm, rock, or integration tests.
Run every test below for each code contribution. The final test rebuilds and
deploys the rock and charm.

Prerequisites
-------------

Complete :ref:`Set up a local Linux environment
<set-up-a-local-linux-environment>` first.

The Go service is under ``app/``. ``app/rockcraft.yaml`` packages it as a rock,
and the charm under ``app/charm/`` operates that image with Juju. See
:ref:`Juju charms and rocks <juju-charms-and-rocks>` for background.

Run all tests
-------------

Run the Go checks:

.. code-block:: bash

   cd ~/gopkg-charm/app
   test -z "$(gofmt -l .)"
   go vet ./...
   go build ./...
  go test -race ./...

Next, run the charm checks:

.. code-block:: bash

   cd ~/gopkg-charm/app/charm
   tox -e lint,unit,static

Finally, rebuild, deploy, and test the rock and charm:

.. code-block:: bash

   cd ~/gopkg-charm
   app/charm/tests/integration/run_full_local_suite.sh

Success ends with ``Full local Juju integration suite completed``. For manual
steps, see :ref:`full-integration-suite-local`.

Update the documentation
------------------------

Update the documentation when a code change affects configuration, deployment,
commands, or user-visible behavior. Follow :ref:`improve-documentation` for
those changes.
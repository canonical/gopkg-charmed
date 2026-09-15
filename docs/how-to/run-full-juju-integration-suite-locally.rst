.. _run-full-juju-integration-suite-locally:
.. _full-integration-suite-local:

.. meta::
   :description: Build the rock and charm, deploy them with Juju, and run the full gopkg-charmed integration suite locally.

How to run the full Juju integration suite locally
==================================================

The full suite catches failures across packaging, deployment, and service
behavior before they reach CI. It verifies that the rock and charm build for
your architecture, that Juju can deploy the charm with the local image
resource, and that the integration tests reach active status and validate
service behavior. Run one script to build the rock and charm, deploy them
with Juju, and execute the integration tests on Linux, on AMD64 or ARM64.

Prerequisites
-------------

Complete :ref:`set-up-a-local-linux-environment`, which installs the tools
this guide needs: ``microk8s``, ``juju``, ``rockcraft``, ``charmcraft``, and
``tox``. The suite requires Linux; on macOS or Windows, run it inside the
Multipass VM from that guide.

Besides the charm itself, the suite deploys ``nginx-ingress-integrator``,
``loki-k8s``, ``prometheus-k8s``, and ``grafana-k8s`` from Charmhub, so the
machine needs internet access and the memory recommended in the setup guide.
The three observability charms are published for amd64 only; on an arm64
host, such as an Apple Silicon VM, their tests are skipped and the rest of
the suite runs.

Run the suite with one command
------------------------------

From the repository root:

.. code-block:: bash

   cd ~/gopkg-charm
   app/charm/tests/integration/run_full_local_suite.sh

The script verifies the operating system and the required commands, detects
the architecture, ensures MicroK8s readiness and the required add-ons,
ensures that a Juju controller is available, builds and pushes the
architecture-matching rock, builds the charm, and runs the integration tox
environment with ``CHARM_FILE`` and ``APP_IMAGE`` set.

If ``rockcraft pack`` fails with a ``PermissionError`` under
``app/charm/.tox``, see :ref:`troubleshoot-deployment`.

Run the suite manually
----------------------

Use the individual steps when you need fine-grained control, for example to
rebuild only one artifact. The first block confirms the environment from
:ref:`set-up-a-local-linux-environment` and bootstraps a controller only if
none exists yet:

.. code-block:: bash

   cd ~/gopkg-charm
   microk8s status --wait-ready
   curl --fail --silent --show-error --retry 30 --retry-delay 2 \
     --retry-all-errors http://127.0.0.1:32000/v2/
   juju controllers >/dev/null 2>&1 || juju bootstrap microk8s dev

   cd ~/gopkg-charm/app
   ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true rockcraft pack
   rockcraft.skopeo copy --insecure-policy --dest-tls-verify=false --dest-no-creds \
     oci-archive:gopkg_0.1_$(dpkg --print-architecture).rock \
     docker://localhost:32000/gopkg:0.1

   cd ~/gopkg-charm/app/charm
   CHARMCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true charmcraft pack
   CHARM_FILE=$(ls -1 gopkg-charmed_*.charm | head -n1)
   CHARM_FILE="$CHARM_FILE" APP_IMAGE=localhost:32000/gopkg:0.1 \
     tox --workdir ~/.cache/gopkg-charm-tox -e integration

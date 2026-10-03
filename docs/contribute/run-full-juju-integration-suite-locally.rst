.. _run-full-juju-integration-suite-locally:
.. _full-integration-suite-local:

.. meta::
   :description: Run the full gopkg-k8s integration suite locally on Canonical Kubernetes, in a VM prepared the way CI prepares its runners.

How to run the full Juju integration suite locally
==================================================

The full suite catches failures across packaging, deployment, and service
behavior before they reach CI. It verifies that the rock and charm build for
your architecture, that Juju can deploy the charm with the local image
resource, and that the integration tests reach active status and validate
service behavior.

CI runs the suite on Canonical Kubernetes, once on Juju 3 and once on
Juju 4, as :ref:`ci-workflows` describes. The script in this guide prepares
the machine from the same concierge files that CI uses, so a local run meets
the same cluster, ingress controller, and Juju version.

Prerequisites
-------------

The script installs Canonical Kubernetes, Juju, LXD, and the build tools
with ``sudo``, and Canonical Kubernetes cannot run next to MicroK8s. Run it
in a fresh Ubuntu 24.04 LTS virtual machine, not in the development VM from
:ref:`set-up-a-development-environment`. On any host with
`Multipass <https://canonical.com/multipass>`_, create and enter one:

.. code-block:: bash

   multipass launch 24.04 --cpus 4 --memory 16G --disk 50G --name gopkg-suite
   multipass shell gopkg-suite

The VM gets the CPUs and memory of the GitHub runners that CI uses. On an
arm64 host, where the observability tests are skipped, 8 GB of memory is
enough.

Inside the VM, clone the repository:

.. code-block:: bash

   git clone https://github.com/canonical/gopkg-charmed.git gopkg-charm

To test changes that are not on GitHub yet, mount your checkout instead, as
:ref:`set-up-a-development-environment` describes, with ``gopkg-suite`` as
the VM name.

Besides the charm itself, the suite deploys ``nginx-ingress-integrator``,
``loki-k8s``, ``prometheus-k8s``, and ``grafana-k8s`` from Charmhub, so the
VM needs internet access. The three observability charms are published for
amd64 only; on an arm64 host, such as an Apple Silicon VM, their tests are
skipped and the rest of the suite runs.

Run the full suite
------------------

From the repository root, run:

.. code-block:: bash

   cd ~/gopkg-charm
   app/charm/tests/integration/run_full_local_suite.sh

On the first run, the script prepares the VM with
``concierge prepare -c concierge-lxd.yaml``, as CI does: concierge installs
Juju 3, Canonical Kubernetes with its Cilium ingress controller, LXD, and
Charmcraft, and bootstraps a Juju controller. Later runs reuse the
controller and skip this step. The script then deploys a local image
registry on port 32000, builds the rock for the VM's architecture and pushes
it under a new tag, builds the charm, and runs the ``integration`` tox
environment with ``INGRESS_CLASS=cilium``, as CI does. Success ends with
``Full local Juju integration suite completed``.

The first run takes the longest: it prepares the VM and builds the charm's
Python dependencies from source. Later runs reuse the controller and the
build instances, so they mostly spend their time on the tests.

To run the suite on Juju 4, as the second CI run does, create another fresh
VM and select the Juju 4 concierge file:

.. code-block:: bash

   cd ~/gopkg-charm
   CONCIERGE=concierge-juju4.yaml app/charm/tests/integration/run_full_local_suite.sh

The script stops without changing anything when MicroK8s is installed, or
when the VM was prepared for the other Juju version.

If ``rockcraft pack`` fails with a ``PermissionError`` under
``app/charm/.tox``, see :ref:`troubleshoot-development`.

Run the suite manually
----------------------

Use the individual steps when you need fine-grained control, for example to
rebuild only one artifact. Run them in the same shell: the last step uses a
variable set in an earlier one.

Prepare the VM with the concierge file CI uses, then install Rockcraft and
tox, which that file leaves out. For Juju 4, use ``concierge-juju4.yaml``:

.. code-block:: bash

   cd ~/gopkg-charm
   sudo snap install concierge --classic
   sudo concierge prepare -c concierge-lxd.yaml
   sudo snap install rockcraft --classic
   sudo apt update
   sudo apt install --yes tox

Deploy the local image registry and wait until it accepts connections:

.. code-block:: bash

   kubectl apply -f app/charm/tests/integration/local-registry.yaml
   kubectl rollout status deployment/registry \
     -n container-registry --timeout=5m
   curl --fail --silent --show-error --retry 30 --retry-delay 2 \
     --retry-all-errors http://localhost:32000/v2/

The last command prints ``{}``.

Build the rock and push it to the registry under a new tag. Kubernetes
reuses a cached image whose tag has not changed, so a new tag makes the tests
deploy the rock you just built:

.. code-block:: bash

   cd ~/gopkg-charm/app
   ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true rockcraft pack
   APP_IMAGE=localhost:32000/gopkg:$(date +%Y%m%d-%H%M%S)
   rockcraft.skopeo copy --insecure-policy --dest-tls-verify=false --dest-no-creds \
     oci-archive:gopkg_0.1_$(dpkg --print-architecture).rock \
     docker://$APP_IMAGE

Build the charm:

.. code-block:: bash

   cd ~/gopkg-charm/app/charm
   CHARMCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true charmcraft pack

Run the integration tests against the charm and image you just built.
Cilium's ingress controller is not the cluster's default ingress class, so
``INGRESS_CLASS`` names it:

.. code-block:: bash

   CHARM_FILE=$PWD/gopkg-k8s_$(dpkg --print-architecture).charm \
     APP_IMAGE=$APP_IMAGE INGRESS_CLASS=cilium \
     tox --workdir ~/.cache/gopkg-charm-tox -e integration

Each test module deploys into its own temporary model, which is destroyed
when the module finishes. To keep the models for inspection, as CI does, end
the tox command with ``-- --no-juju-teardown tests/integration``. Arguments
after ``--`` replace the default test path, so the command names it again.

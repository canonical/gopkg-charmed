.. _run-full-juju-integration-suite-locally:
.. _full-integration-suite-local:

.. meta::
   :description: Run the gopkg-k8s Juju integration suite locally with tox, in a Multipass VM prepared with charm-ci's tools.

How to run the full Juju integration suite locally
==================================================

The integration tests deploy the charm with Juju and check each of its
integrations, as :ref:`ci-workflows` describes. CI runs them with Canonical's
`charm-ci <https://github.com/canonical/charm-ci>`_; locally, run them with
``tox -e integration``. The tests take the charm and its image from
``build/artifacts.build.yaml`` through charm-ci's ``pytest`` plugin, so the steps
below build both and prepare the machine with charm-ci's ``opcli`` tool and
the concierge file CI uses.

Create a VM
-----------

The charm and the observability charms the tests deploy are published for
AMD64. On an AMD64 host, create and enter a fresh Ubuntu 24.04 LTS VM with
`Multipass <https://canonical.com/multipass>`_, sized like the GitHub runners
CI uses. On an Apple Silicon Mac, rely on your pull request's CI run.

.. code-block:: bash

   multipass launch 24.04 --cpus 4 --memory 16G --disk 50G --name gopkg-suite
   multipass shell gopkg-suite

Keep it separate from the VM in :ref:`set-up-a-development-environment`: the
steps below install Canonical Kubernetes, which cannot run next to MicroK8s.

Inside the VM, clone the repository:

.. code-block:: bash

   git clone https://github.com/canonical/gopkg-charmed.git gopkg-charm

To test changes that are not on GitHub yet, mount your checkout instead, as
:ref:`set-up-a-development-environment` describes, with ``gopkg-suite`` as
the VM name.

Install charm-ci's tools
------------------------

Install ``opcli`` from the charm-ci release that the integration test
workflow pins, then the tools it drives:

.. code-block:: bash

   sudo snap install astral-uv --classic
   uv tool install "opcli[cli] @ git+https://github.com/canonical/charm-ci.git@v1.0.1"
   export PATH="$HOME/.local/bin:$PATH"
   opcli install all

``opcli install all`` adds your user to the ``lxd`` group. Leave the VM with
``exit`` and enter it again with ``multipass shell gopkg-suite`` so the
membership applies.

Build and prepare
-----------------

Build the rock and the charm from ``artifacts.yaml``, prepare the VM from the
concierge file CI uses for Juju 3, and push the rock to a local registry:

.. code-block:: bash

   cd ~/gopkg-charm
   opcli artifacts build
   opcli env provision -c concierge-lxd.yaml
   opcli artifacts push-images --missing-registry deploy

To test on Juju 4, as the second CI run does, use another VM and
``concierge-juju4.yaml``.

Run the tests
-------------

.. code-block:: bash

   cd ~/gopkg-charm/app/charm
   INGRESS_CLASS=cilium tox -e integration

``INGRESS_CLASS=cilium`` is the value CI passes from ``spread.yaml``: the
Cilium ingress controller of Canonical Kubernetes is not the cluster's default
ingress class. Each test module deploys into its own temporary model.

After changing the service, the rock, or the charm, run
``opcli artifacts build`` and
``opcli artifacts push-images --missing-registry deploy`` again from the
repository root before the tests.

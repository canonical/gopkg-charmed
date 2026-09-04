.. _set-up-a-local-linux-environment:

Set up a local Linux environment
================================

A consistent Ubuntu environment keeps local builds and tests aligned with CI.
Prepare a native or virtual machine with the tools needed to build, deploy, and
test ``gopkg-charmed``.

Prerequisites
-------------

The repository's documented and CI-tested environment for the complete code
test path is:

- Ubuntu 24.04 LTS, either on a native Linux host or in a virtual machine
- an ``amd64`` or ``arm64`` processor architecture
- network access for APT, snaps, Go modules, charm dependencies, and OCI images

The rock and charm both declare Ubuntu 24.04 LTS build bases and ``amd64`` and
``arm64`` platforms. The integration runner rejects non-Linux systems and
architectures other than ``amd64`` and ``arm64``.

For a virtual machine, this repository uses and has tested the following
allocation:

- 4 virtual CPUs
- 8 GB of memory
- 50 GB of disk space

These values are the project's tested profile, not claimed minimums. The
repository's deployment testing found that 4 GB of memory can leave the Juju
controller without enough capacity to schedule the charm workloads.

On macOS, use Multipass to create the Ubuntu VM. Current Multipass support
requires macOS 14 or later and supports Intel and Apple-silicon Macs.
See the `Multipass installation guide
<https://canonical.com/multipass/docs/latest/how-to-guides/install-multipass/>`_
before continuing.

Step 1: create and enter a VM
-----------------------------

Skip this step on a native Ubuntu 24.04 LTS host.

.. SPREAD SKIP

.. code-block:: bash

   multipass launch 24.04 --cpus 4 --disk 50G --memory 8G --name charm-dev
   multipass shell charm-dev

.. SPREAD SKIP END

Step 2: make the repository available
-------------------------------------

Choose one of these options.

To mount an existing checkout from the host, leave the VM, run this command on
the host, and then enter the VM again:

.. SPREAD SKIP

.. code-block:: bash

   multipass mount /path/to/gopkg-charm charm-dev:/home/ubuntu/gopkg-charm
   multipass shell charm-dev

Replace ``/path/to/gopkg-charm`` with the absolute path to your checkout.

Alternatively, clone the repository inside the VM:

.. code-block:: bash

   git clone https://github.com/canonical/gopkg-charmed.git gopkg-charm

.. SPREAD SKIP END

Whichever option you chose, enter and verify the repository before continuing:

.. code-block:: bash

   cd ~/gopkg-charm
   git rev-parse --show-toplevel

The final command should return ``/home/ubuntu/gopkg-charm``.

Step 3: install required tools
------------------------------

.. SPREAD SKIP

.. code-block:: bash

   sudo apt update
   sudo apt install --yes curl git python3.12-venv tox
   sudo snap install go --classic
   sudo snap install rockcraft --classic
   sudo snap install charmcraft --classic
   sudo snap install juju
   sudo snap install microk8s --channel 1.31-strict/stable
   sudo adduser $USER snap_microk8s
   lxd init --auto

.. SPREAD SKIP END

Log out of the VM and back in so ``snap_microk8s`` group membership applies:

.. SPREAD SKIP

.. code-block:: bash

   exit
   multipass shell charm-dev
   id -nG | grep -qw snap_microk8s

.. SPREAD SKIP END

The final command must exit successfully before you continue. Alternatively,
run ``newgrp snap_microk8s`` to open a shell with the new group membership.

Step 4: enable Kubernetes add-ons
---------------------------------

.. code-block:: bash

   sudo microk8s enable hostpath-storage registry ingress
   microk8s status --wait-ready
   microk8s kubectl rollout status deployment/registry \
     -n container-registry --timeout=5m
   curl --fail http://127.0.0.1:32000/v2/

The add-ons must appear under ``enabled`` in the status output. The final
command should return ``{}``, confirming that the registry is accepting
connections before you build or publish an image.

Optional: clean local-only Python artifacts
-------------------------------------------

If you mounted a checkout that contains Python environments created on another
OS, remove those generated artifacts before building rocks:

.. code-block:: bash

   cd ~/gopkg-charm
   rm -rf app/charm/.tox app/charm/.venv

This prevents ``rockcraft pack`` errors caused by incompatible interpreter
files entering Rockcraft's build instance. A repository cloned inside the VM
does not need this cleanup unless it contains copied environments.

Step 5: verify the repository and tools
---------------------------------------

.. code-block:: bash

   cd ~/gopkg-charm
   command -v curl
   command -v go
   command -v juju
   command -v charmcraft
   command -v rockcraft
   command -v microk8s
   command -v tox
   command -v lxd
   id -nG | grep -qw snap_microk8s
   dpkg --print-architecture
   git rev-parse --show-toplevel
   test -f app/rockcraft.yaml
   test -f app/charm/charmcraft.yaml

Expected architecture is ``amd64`` or ``arm64``.

Next steps
----------

- For deployment flow: :ref:`deploy-and-verify-on-kubernetes`
- For full integration tests: :ref:`full-integration-suite-local`
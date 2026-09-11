.. _set-up-a-local-linux-environment:

.. meta::
   :description: Prepare an Ubuntu environment with the tools and resources required to build, deploy, and test gopkg-charmed.

How to set up a local Linux environment
=======================================

A consistent Ubuntu environment keeps local builds and tests aligned with CI.
Prepare a virtual machine with the tools needed to build, deploy, and test
``gopkg-charmed``.

Prerequisites
-------------

You will need a workstation, for example a laptop, with AMD64 or ARM64
architecture. Your workstation should have at least 4 CPU cores, 8 GB of RAM,
50 GB of disk space, and network access for APT, snaps, Go modules, charm
dependencies, and OCI images.

This guide uses `Multipass <https://canonical.com/multipass>`_ to create an
Ubuntu 24.04 LTS virtual machine. Multipass runs on Linux, macOS, and Windows,
so the same steps apply on every host. Install it by following the `Multipass
installation guide
<https://canonical.com/multipass/docs/latest/how-to-guides/install-multipass/>`_
before continuing. If your workstation already runs Ubuntu 24.04 LTS, you can
skip the virtual machine and run the remaining steps directly on it.

Create and enter a VM
---------------------

Skip this section if your workstation already runs Ubuntu 24.04 LTS.

.. SPREAD SKIP

.. code-block:: bash

   multipass launch 24.04 --cpus 4 --disk 50G --memory 8G --name charm-dev
   multipass shell charm-dev

.. SPREAD SKIP END

Make the repository available
-----------------------------

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

Install required tools
----------------------

.. code-block:: bash

   sudo apt update
   sudo apt install --yes curl git python3.12-venv tox
   sudo snap install go --classic
   sudo snap install lxd
   sudo snap install rockcraft --classic
   sudo snap install charmcraft --classic
   sudo snap install juju --channel 3/stable
   sudo snap install microk8s --channel 1.36-strict/stable
   sudo adduser $USER snap_microk8s
   sudo adduser $USER lxd

Log out of the VM and back in so the new group memberships apply:

.. SPREAD SKIP

.. code-block:: bash

   exit
   multipass shell charm-dev

.. SPREAD SKIP END

.. SPREAD
   # spread-session-break
.. SPREAD END

Confirm the new group memberships in the new session, then initialize LXD:

.. code-block:: bash

   id -nG | grep -qw snap_microk8s
   id -nG | grep -qw lxd
   lxd init --auto

The commands must exit successfully before you continue. In an interactive
shell, ``newgrp snap_microk8s`` also applies the membership, but it opens a
new shell: do not paste further commands after it.

Enable Kubernetes add-ons
-------------------------

.. code-block:: bash

   microk8s status --wait-ready
   sudo microk8s enable dns hostpath-storage registry ingress
   microk8s status --wait-ready
   microk8s kubectl rollout status deployment/registry \
     -n container-registry --timeout=15m
   curl --fail --silent --show-error --retry 30 --retry-delay 2 \
     --retry-all-errors http://127.0.0.1:32000/v2/

The add-ons must appear under ``enabled`` in the status output. The final
command returns ``{}``, confirming that the registry is accepting connections
before you build or publish an image. It retries for up to a minute because
the registry can take a few seconds to accept connections after the
deployment finishes rolling out.

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

Verify the repository and tools
-------------------------------

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
   id -nG | grep -qw lxd
   dpkg --print-architecture
   git rev-parse --show-toplevel
   test -f app/rockcraft.yaml
   test -f app/charm/charmcraft.yaml

The architecture command prints AMD64 or ARM64.

Next steps
----------

- For deployment flow: :ref:`deploy-and-verify-on-kubernetes`
- For full integration tests: :ref:`full-integration-suite-local`
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
so the same steps apply on every host, and the VM keeps everything the guide
installs separate from your workstation. Install it by following
:ref:`Install Multipass <multipass:how-to-guides-install-multipass>` before
continuing.

If your workstation already runs Ubuntu 24.04 LTS, you can skip the virtual
machine and run the remaining steps directly on it. Be aware of what that
means: the steps install packages and snaps with ``sudo``, add your user to
the ``snap_microk8s`` and ``lxd`` groups, and start a MicroK8s cluster whose
add-ons listen on ports 80, 443, and 32000 of the workstation.

Create and enter a VM
---------------------

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

Building, deploying, and testing ``gopkg-charmed`` needs Go for the service,
Python 3.12 and tox for the charm tests, Rockcraft and Charmcraft to build the
rock and the charm (both build inside LXD), Juju and MicroK8s to deploy them,
and curl and git for the commands in the guides.
:ref:`platforms-and-prerequisites` lists the channels and the versions the
guides were last verified with. Install everything:

.. code-block:: bash

   sudo apt update
   sudo apt install --yes curl git python3.12-venv tox
   sudo snap install go --classic
   sudo snap install lxd
   sudo snap install rockcraft --classic
   sudo snap install charmcraft --classic
   sudo snap install juju --channel 3/stable
   sudo snap install microk8s --channel 1.36-strict/stable

MicroK8s and LXD only accept commands from members of their groups, so add
your user to both:

.. code-block:: bash

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

If both memberships apply, none of the commands print anything.

.. note::

   In an interactive shell, ``newgrp snap_microk8s`` applies the membership
   without logging out. It starts a new shell, so any commands you paste
   together with it run in the original shell, before the membership applies.

Enable Kubernetes add-ons
-------------------------

The deployment needs four MicroK8s add-ons: ``dns`` for name resolution
inside the cluster, ``hostpath-storage`` for the volumes the Juju controller
requests, ``registry`` for the local image registry on port 32000 that
receives the rock, and ``ingress`` for the NGINX ingress controller that
publishes the service on ports 80 and 443. Wait for the cluster, then enable
them:

.. code-block:: bash

   microk8s status --wait-ready
   sudo microk8s enable dns hostpath-storage registry ingress

Confirm that the add-ons are enabled and that the registry accepts
connections:

.. code-block:: bash

   microk8s status --wait-ready
   microk8s kubectl rollout status deployment/registry \
     -n container-registry --timeout=15m
   curl --fail --silent --show-error --retry 30 --retry-delay 2 \
     --retry-all-errors http://127.0.0.1:32000/v2/

The status output lists the four add-ons under ``enabled``, the second
command ends with ``deployment "registry" successfully rolled out``, and the
final command prints ``{}``. That last command retries for up to a minute
because the registry can take a few seconds to accept connections after the
deployment finishes rolling out.

Optional: clean local-only Python artifacts
-------------------------------------------

If you mounted a checkout that contains Python environments created on another
OS, remove those generated artifacts before building the rock:

.. code-block:: bash

   cd ~/gopkg-charm
   rm -rf app/charm/.tox app/charm/.venv

This prevents ``rockcraft pack`` errors caused by incompatible interpreter
files entering Rockcraft's build instance. A repository cloned inside the VM
does not need this cleanup unless it contains copied environments.

Confirm the tools
-----------------

Check that every tool is on the path and that the checkout contains the two
build recipes:

.. code-block:: bash

   cd ~/gopkg-charm
   command -v curl go juju charmcraft rockcraft microk8s tox lxd
   dpkg --print-architecture
   test -f app/rockcraft.yaml
   test -f app/charm/charmcraft.yaml

The first command prints one path per tool, ``dpkg`` prints ``amd64`` or
``arm64``, and the two ``test`` commands print nothing.

Next steps
----------

- Follow the step-by-step tutorial :ref:`deploy-and-verify-on-kubernetes`
  to build, deploy, and verify the charm in this environment.
- Run the integration tests with :ref:`full-integration-suite-local`.

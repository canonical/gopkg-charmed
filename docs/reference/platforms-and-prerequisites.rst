.. _platforms-and-prerequisites:

.. meta::
   :description: Reference the supported architectures, required tools and channels, MicroK8s add-ons, and verified tool versions for gopkg-charmed.

Platforms and prerequisites
===========================

Supported architectures
-----------------------

This project supports both AMD64 and ARM64.

Required tooling for charm deployment
-------------------------------------

The guides install these tools from the following snap channels:

- ``rockcraft`` from ``latest/stable``
- ``charmcraft`` from ``latest/stable``
- ``juju`` from ``3/stable``
- ``microk8s`` from ``1.36-strict/stable``
- ``lxd`` from its default channel, initialized with ``lxd init --auto``

Both craft tools need their experimental extensions enabled, which the guides
do with ``ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true`` and
``CHARMCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true``.

The documentation tests last verified the guides with Charmcraft 4.4.1,
Rockcraft 1.20.0, Juju 3.6.28, MicroK8s 1.36.2, and LXD 5.21.7. Newer
releases from the same channels are expected to work; older releases are
untested.

MicroK8s add-ons
----------------

The following add-ons must be enabled before deploying:

- ``dns``
- ``hostpath-storage``
- ``registry``
- ``ingress``

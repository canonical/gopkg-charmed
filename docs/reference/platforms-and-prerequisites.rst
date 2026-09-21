.. _platforms-and-prerequisites:

.. meta::
   :description: Reference the supported architectures, required tools and channels, MicroK8s add-ons, and verified tool versions for gopkg-k8s.

Platforms and prerequisites
===========================

Supported architectures
-----------------------

The charm and the ``app-image`` resource on Charmhub are AMD64: CI builds and
publishes AMD64 only, and ``app/rockcraft.yaml`` and
``app/charm/charmcraft.yaml`` declare ``amd64`` alone. The guides also work
on ARM64 when you build locally; uncomment ``arm64`` under ``platforms`` in
both recipes first. The observability charms are published for AMD64 only,
so :ref:`integrate-with-cos` needs an AMD64 machine.

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

The documentation tests last verified the guides with Charmcraft 4.4.2,
Rockcraft 1.20.0, Juju 3.6.28, MicroK8s 1.36.2, LXD 5.21.7, and Go 1.26.7
from the ``go`` snap. Newer releases from the same channels are expected to
work; older releases are untested.

The artifacts pin what they are built on: the charm uses the ``ubuntu@24.04``
base, the rock builds on ``ubuntu@24.04`` but ships with ``base: bare``, the
Go module requires Go 1.21.2 or later, and the charm depends on ``ops`` 3.8
and ``paas-charm`` 1.x.

MicroK8s add-ons
----------------

The following add-ons must be enabled before deploying:

- ``dns``
- ``hostpath-storage``
- ``registry``
- ``ingress``

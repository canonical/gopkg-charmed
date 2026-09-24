.. _platforms-and-prerequisites:

.. meta::
   :description: Reference the supported architectures, required tools and channels, MicroK8s add-ons, and verified tool versions for gopkg-k8s.

Platforms and prerequisites
===========================

Supported architectures
-----------------------

The charm and its ``app-image`` resource on Charmhub are built for AMD64
only. Building
from source works on AMD64 and ARM64: ``app/rockcraft.yaml`` and
``app/charm/charmcraft.yaml`` declare both, and :ref:`improve-code` covers
the build. The observability charms are published for AMD64 only, so
:ref:`integrate-with-cos` needs an AMD64 machine as well.

Required tooling
----------------

Deploying the charm requires the following snaps:

- ``juju`` from ``3/stable``
- ``microk8s`` from ``1.36-strict/stable``

Building from source, covered by :ref:`set-up-a-development-environment` and
:ref:`improve-code`, adds:

- ``rockcraft`` from ``latest/stable``
- ``charmcraft`` from ``latest/stable``
- ``lxd`` from its default channel, initialized with ``lxd init --auto``
- ``go`` from ``latest/stable``, and ``tox`` for the charm tests

Both craft tools need experimental extensions enabled, which
requires ``ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true``
and ``CHARMCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true``.

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

A deployment on MicroK8s needs these add-ons:

- ``dns``, which resolves names inside the cluster
- ``hostpath-storage``, which provides the volumes the Juju controller
  requests
- ``ingress``, which runs the ingress controller that publishes the service

Building from source also needs ``registry``, the local image registry on
port 32000 that receives the rock.

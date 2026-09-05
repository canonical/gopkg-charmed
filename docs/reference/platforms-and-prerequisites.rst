.. _platforms-and-prerequisites:

.. meta::
   :description: Reference supported architectures, required charm deployment tools, MicroK8s add-ons, and Juju model constraints.

Platforms and prerequisites
===========================

Supported architectures
-----------------------

This project supports both:

- ``amd64``
- ``arm64``

You can check your architecture with:

.. code-block:: bash

   dpkg --print-architecture

Required tooling for charm deployment
-------------------------------------

- ``rockcraft``
- ``charmcraft``
- ``juju`` from channel ``3/stable``
- ``microk8s`` from channel ``1.31-strict/stable``
- ``lxd`` initialized with ``lxd init --auto``

MicroK8s add-ons
----------------

Enable these add-ons before deploying:

- ``dns``
- ``hostpath-storage``
- ``registry``
- ``ingress``

Juju model constraints
----------------------

Always set model constraints before deployment to avoid architecture scheduling
mismatches:

.. code-block:: bash

   juju set-model-constraints arch=$(dpkg --print-architecture)

.. _explanation:

.. meta::
	:description: Understand how gopkg.in resolves imports and how ingress exposes gopkg-k8s.

Explanation
===========

Understand what the service does and how ``gopkg-k8s`` is exposed:

- Learn what ``gopkg.in`` does for a Go program and why its import paths
  still matter in :doc:`How gopkg.in serves stable import paths
  <gopkg-service>`.
- Follow request routing from the client to the workload in
  :doc:`Ingress <ingress>`.

For Juju, charms, and rocks themselves, see the `Juju
<https://canonical.com/juju/docs/juju-cli/3.6/reference/juju/>`_,
`Charmcraft <https://canonical.com/juju/docs/charmcraft/4/>`_ and
`Rockcraft <https://ubuntu.com/containers/rockcraft/docs/latest/>`_
documentation.

.. vale off

.. toctree::
	:maxdepth: 1

	gopkg-service
	ingress

.. vale on

.. _explanation:

.. meta::
	:description: Understand how gopkg.in resolves imports and how rocks, charms, Juju, and ingress package, operate, and expose gopkg-charmed.

Explanation
===========

Understand what the service does and how ``gopkg-charmed`` is packaged,
operated, and exposed:

- Learn what ``gopkg.in`` does for a Go program and why its import paths
  still matter in :doc:`How gopkg.in serves stable import paths
  <gopkg-service>`.
- Learn the packaging and orchestration concepts in :doc:`Juju, charms, and
  rocks <juju-charms-and-rocks>`.
- Follow request routing from the client to the workload in
  :doc:`Ingress <ingress>`.

.. vale off

.. toctree::
	:maxdepth: 1

	gopkg-service
	juju-charms-and-rocks
	ingress

.. vale on

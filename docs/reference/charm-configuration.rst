.. _charm-configuration:

.. meta::
   :description: Reference the gopkg-k8s hostname option, its default value, and how it maps to the workload.

Charm configuration
===================

The charm declares one application-specific option:

``hostname``
  Type: string

  Default: ``gopkg.in``

  Value passed to the workload as ``APP_HOSTNAME``. It controls the hostname
  rendered in package links and ``go-import`` metadata.

To change it and verify the result, follow
:ref:`configure-hostname-and-check-go-import`.

Running ``juju config gopkg-k8s`` also lists the options that the Go
framework extension adds when the charm is packed: ``app-secret-key``, a
secret-typed option that takes a Juju user secret ID. The application port
and the metrics port and path are not charm options; they are set in the
charm's ``paas-config.yaml`` and default to ``8080``, ``8080`` and
``/metrics``. The observability settings are described in
:ref:`integrations`, and
:ref:`charmcraft:go-framework-extension-config-options` documents the
extension's full set.

Ingress routing is configured on the ``nginx-ingress-integrator`` charm, not
on ``gopkg-k8s``. See :ref:`configure-ingress` for the settings this
deployment uses and the `NGINX ingress integrator configuration reference
<https://charmhub.io/nginx-ingress-integrator/configurations>`_ for every
option.

.. _charm-configuration:

.. meta::
   :description: Reference the gopkg-charmed hostname option, its default value, and how it maps to the workload.

Charm configuration
===================

The charm exposes one application-specific option. To change it and verify
the result, follow :ref:`configure-hostname-and-check-go-import`.

``hostname``
  Type: string

  Default: ``gopkg.in``

  Value passed to the workload as ``APP_HOSTNAME``. It controls the hostname
  rendered in package links and ``go-import`` metadata.

Ingress routing is configured on the ``nginx-ingress-integrator`` charm, not
on ``gopkg-charmed``. See :ref:`configure-ingress` for the settings this
deployment uses and the `NGINX ingress integrator configuration reference
<https://charmhub.io/nginx-ingress-integrator/configurations>`_ for every
option.

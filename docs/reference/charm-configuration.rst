.. _charm-configuration:

.. meta::
   :description: Reference the gopkg-charmed hostname option, default value, workload mapping, and update behavior.

Charm configuration
===================

gopkg-charmed config options
----------------------------

The charm currently exposes one application-specific option:

``hostname``
  Type: string

  Default: ``gopkg.in``

  Meaning: value passed to the workload as ``APP_HOSTNAME``. It controls
  hostname rendering in package links and go-import metadata.

Set configuration
-----------------

.. code-block:: bash

   juju config gopkg-charmed hostname=staging.example.com

Inspect configuration
---------------------

.. code-block:: bash

   juju config gopkg-charmed

Ingress settings used with this charm
-------------------------------------

When using ``nginx-ingress-integrator``, the most relevant settings are:

- ``service-hostname``: hostname used for ingress routing
- ``path-routes``: route mapping, typically ``/``
- ``rewrite-enabled``: should be ``false`` for this workload

.. _configure-hostname-and-check-go-import:

.. meta::
   :description: Set the ingress and workload hostname of gopkg-charmed, then verify the go-import metadata served to Go clients.

How to configure hostname
=========================

Correct hostname metadata lets Go clients discover source through the stable
``gopkg.in`` import path. Set the workload hostname, then query a package
path to verify the generated ``go-import`` metadata.

Two settings carry a hostname. ``service-hostname``, on
``nginx-ingress-integrator``, decides which incoming requests reach the
application. ``hostname``, on ``gopkg-charmed``, is the name the workload
writes into its ``go-import`` metadata and package links. This guide changes
the second one and queries the service through the first.
:ref:`Ingress <ingress>` explains why they are separate settings.

Prerequisites
-------------

This guide changes a running deployment, so it needs:

- ``gopkg-charmed`` and ``nginx-ingress-integrator`` deployed and integrated
- the integrator's ``service-hostname`` set to the hostname clients use
- that same hostname exported as ``INGRESS_HOST``, which every command below
  reuses

The deployment steps of :ref:`deploy-and-verify-on-kubernetes` leave the
first two in place, using ``gopkg.example.com``. Export it:

.. code-block:: bash

   export INGRESS_HOST=gopkg.example.com

For local verification, requests are routed to ``127.0.0.1`` with
``--resolve``.

Change the hostname configuration
---------------------------------

.. code-block:: bash

   juju config gopkg-charmed hostname=staging.example.com

The charm applies the new value by restarting the workload in place, which
usually takes a couple of minutes. Wait until the application is active
again:

.. SPREAD SKIP

.. code-block:: bash

   juju status --watch 2s

.. SPREAD SKIP END

.. SPREAD
   juju wait-for application gopkg-charmed \
     --query='status=="active"' --timeout=15m
.. SPREAD END

Confirm the stored value
------------------------

.. code-block:: bash

   juju config gopkg-charmed hostname

The command prints ``staging.example.com``.

Verify the change
-----------------

Check that the service still answers through ingress:

.. code-block:: bash

    curl --fail --silent --show-error --retry 30 --retry-delay 2 \
       --retry-all-errors \
     http://${INGRESS_HOST}/health-check \
     --resolve ${INGRESS_HOST}:80:127.0.0.1 | grep -Fx ok

Expected output is ``ok``.

Then check the metadata the service serves to Go clients. The restart means
the old value can be served for a few more seconds, so query until the new
value appears (the loop gives up after two minutes):

.. code-block:: bash

   timeout 120 bash -c '
     until curl --fail --silent --show-error \
         "http://${INGRESS_HOST}/yaml.v2?go-get=1" \
         --resolve "${INGRESS_HOST}:80:127.0.0.1" \
         | grep "go-import.*staging.example.com"; do
       sleep 5
     done
   '

The output contains a ``go-import`` meta tag reflecting the configured
hostname.

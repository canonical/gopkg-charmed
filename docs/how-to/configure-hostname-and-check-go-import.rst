.. _configure-hostname-and-check-go-import:

.. meta::
   :description: Configure ingress and workload hostname values, then verify the go-import metadata served to Go clients.

Configure hostname and verify go-import metadata
================================================

Correct hostname metadata lets Go clients discover source through the stable
``gopkg.in`` import path. Set the ingress and workload hostname values, then
query a package path to verify the generated ``go-import`` metadata.

These steps assume that ``gopkg-charmed`` and ``nginx-ingress-integrator``
are deployed and integrated, as they are at the end of
:ref:`deploy-and-verify-on-kubernetes`.

Set an ingress host for local checks
------------------------------------

.. code-block:: bash

   export INGRESS_HOST=gopkg.example.com
   juju config nginx-ingress-integrator service-hostname=${INGRESS_HOST}

For local verification, requests are routed to ``127.0.0.1`` with ``--resolve``.

Change the hostname configuration
---------------------------------

.. code-block:: bash

   juju config gopkg-charmed hostname=staging.example.com

Wait until the application is active again:

.. SPREAD SKIP

.. code-block:: bash

   juju status --watch 2s

.. SPREAD SKIP END

.. SPREAD
   juju wait-for application gopkg-charmed \
     --query='status=="active"' --timeout=15m
.. SPREAD END

Inspect the configuration
-------------------------

Show every option with its current value:

.. code-block:: bash

   juju config gopkg-charmed

Verify the health endpoint
--------------------------

.. code-block:: bash

    curl --fail --silent --show-error --retry 30 --retry-delay 2 \
       --retry-all-errors \
     http://${INGRESS_HOST}/health-check \
     --resolve ${INGRESS_HOST}:80:127.0.0.1 | grep -Fx ok

Expected output is ``ok``.

Verify the go-import metadata
-----------------------------

The charm delivers the new hostname by restarting the workload in place,
so the old value can be served for a few more seconds. Query until the
new value appears (the loop gives up after two minutes):

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

.. _configure-hostname-and-check-go-import:

.. meta::
   :description: Configure ingress and workload hostname values, then verify the go-import metadata served to Go clients.

Configure hostname and verify go-import metadata
================================================

Correct hostname metadata lets Go clients discover source through the stable
``gopkg.in`` import path. Set the ingress and workload hostname values, then
query a package path to verify the generated ``go-import`` metadata.

Prerequisites
-------------

Complete :ref:`set-up-a-local-linux-environment`, then
:ref:`Deploy locally with MicroK8s and Juju <deploy-locally-with-microk8s>`.

Set an ingress host for local checks
------------------------------------

.. code-block:: bash

   export INGRESS_HOST=gopkg.example.com
   juju config nginx-ingress-integrator service-hostname=${INGRESS_HOST}

For local verification, requests are routed to ``127.0.0.1`` with ``--resolve``.

Change hostname config
----------------------

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

Verify health endpoint
----------------------

.. code-block:: bash

    curl --fail --silent --show-error --retry 30 --retry-delay 2 \
       --retry-all-errors \
     http://${INGRESS_HOST}/health-check \
     --resolve ${INGRESS_HOST}:80:127.0.0.1 | grep -Fx ok

Expected output is ``ok``.

Verify go-import metadata
-------------------------

.. code-block:: bash

    curl --fail --silent --show-error --retry 30 --retry-delay 2 \
       --retry-all-errors \
     "http://${INGRESS_HOST}/yaml.v2?go-get=1" \
       --resolve ${INGRESS_HOST}:80:127.0.0.1 | \
       grep 'go-import.*staging.example.com'

Expected output contains a ``go-import`` meta tag and should reflect the
configured hostname.

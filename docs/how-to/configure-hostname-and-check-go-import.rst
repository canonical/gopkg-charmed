.. _configure-hostname-and-check-go-import:

Configure hostname and verify go-import metadata
================================================

This guide explains how to change the charm hostname config and verify that
the application serves expected import metadata.

If this is your first run on a machine, complete
:ref:`set-up-a-local-linux-environment` first.

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

.. code-block:: bash

   juju status --watch 2s

Verify health endpoint
----------------------

.. code-block:: bash

    curl -sw '\nHTTP %{http_code}\n' http://${INGRESS_HOST}/health-check \
       --resolve ${INGRESS_HOST}:80:127.0.0.1

Expected output includes:

- ``ok``
- ``HTTP 200``

Verify go-import metadata
-------------------------

.. code-block:: bash

    curl -s "http://${INGRESS_HOST}/yaml.v2?go-get=1" \
       --resolve ${INGRESS_HOST}:80:127.0.0.1

Expected output contains a ``go-import`` meta tag and should reflect the
configured hostname.

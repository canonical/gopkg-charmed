.. _configure-hostname-and-check-go-import:

Configure hostname and verify go-import metadata
================================================

This guide explains how to change the charm hostname config and verify that
the application serves expected import metadata.

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

   curl -sw '\nHTTP %{http_code}\n' http://gopkg.example.com/health-check \
     --resolve gopkg.example.com:80:127.0.0.1

Expected output includes:

- ``ok``
- ``HTTP 200``

Verify go-import metadata
-------------------------

.. code-block:: bash

   curl -s "http://gopkg.example.com/yaml.v2?go-get=1" \
     --resolve gopkg.example.com:80:127.0.0.1

Expected output contains a ``go-import`` meta tag and should reflect the
configured hostname.

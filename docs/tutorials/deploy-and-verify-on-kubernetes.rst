.. _deploy-and-verify-on-kubernetes:

.. meta::
   :description: Build the gopkg-charmed rock and charm, deploy them on Kubernetes with Juju, and verify ingress and go-import metadata.

Deploy and verify gopkg-charmed on Kubernetes
=============================================

An end-to-end deployment shows how the Go service, rock, charm, Juju, and
ingress work together. Build the artifacts, deploy them on Kubernetes, and
verify the service on ``amd64`` or ``arm64``.

What you will build
-------------------

At the end of this tutorial, you will have:

- a running ``gopkg-charmed`` application in a Juju model
- an ingress integration for external routing
- a verified health endpoint and a verified go-import metadata endpoint

Prerequisites
-------------

Complete :ref:`set-up-a-local-linux-environment`. That guide creates the Linux
environment, makes the repository available by mount or clone, and installs
the required tools.

Enter the repository root before continuing:

.. code-block:: bash

   cd ~/gopkg-charm

Confirm that MicroK8s access and the local registry are ready:

.. code-block:: bash

   id -nG | grep -qw snap_microk8s
   microk8s status --wait-ready
   microk8s kubectl rollout status deployment/registry \
     -n container-registry --timeout=5m
   curl --fail http://127.0.0.1:32000/v2/

The last command should return ``{}``. If it cannot connect, return to the
add-on step in :ref:`set-up-a-local-linux-environment`; do not continue to the
image push.

Bootstrap Juju only after these checks pass:

.. code-block:: bash

   juju bootstrap microk8s dev

Step 1: confirm architecture
----------------------------

Use this command and keep the result for later commands:

.. code-block:: bash

   dpkg --print-architecture

Expected values are ``amd64`` or ``arm64``.

Step 2: build and publish the rock image
----------------------------------------

From the repository root:

.. code-block:: bash

   cd ~/gopkg-charm/app
   ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true rockcraft pack
   curl --fail http://127.0.0.1:32000/v2/
   rockcraft.skopeo copy --insecure-policy --dest-tls-verify=false --dest-no-creds \
     oci-archive:gopkg_0.1_$(dpkg --print-architecture).rock \
     docker://localhost:32000/gopkg:0.1

Verify image push:

.. code-block:: bash

   curl --fail --silent --show-error \
     http://localhost:32000/v2/gopkg/tags/list | grep -F '"0.1"'

Expected output contains ``"0.1"``. The command exits with a failure if the
registry does not contain the image tag.

Step 3: build the charm
-----------------------

.. code-block:: bash

   cd ~/gopkg-charm/app/charm
   CHARMCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true charmcraft pack
   ls -1 gopkg-charmed_*.charm

The final command must print the path to the packed charm.

Step 4: deploy to a new model
-----------------------------

.. code-block:: bash

   juju add-model gopkg-charmed
   juju set-model-constraints arch=$(dpkg --print-architecture)

Deploy the charm and ingress integrator:

.. code-block:: bash

   cd ~/gopkg-charm/app/charm
   juju deploy ./gopkg-charmed_*.charm gopkg-charmed \
     --resource app-image=localhost:32000/gopkg:0.1
   juju deploy nginx-ingress-integrator --channel=latest/stable --trust
   juju integrate nginx-ingress-integrator gopkg-charmed

Choose an ingress hostname:

.. code-block:: bash

   export INGRESS_HOST=gopkg.example.com

``gopkg.example.com`` is a safe documentation hostname. It does not create DNS
records by itself. For this local tutorial, requests are pinned to
``127.0.0.1`` with ``--resolve`` so the workflow is copy-paste runnable on a
fresh Ubuntu environment.

Configure ingress:

.. code-block:: bash

   juju config nginx-ingress-integrator \
      service-hostname=${INGRESS_HOST} \
     path-routes=/ \
     rewrite-enabled=false

Wait for active status:

.. SPREAD SKIP

.. code-block:: bash

   juju status --watch 2s

.. SPREAD SKIP END

.. SPREAD
   juju wait-for application gopkg-charmed \
     --query='status=="active"' --timeout=15m
   juju wait-for application nginx-ingress-integrator \
     --query='status=="active"' --timeout=15m
.. SPREAD END

Step 5: verify the deployment
-----------------------------

Run a health check through ingress:

.. code-block:: bash

   curl --fail --silent --show-error \
     http://${INGRESS_HOST}/health-check \
     --resolve ${INGRESS_HOST}:80:127.0.0.1 | grep -Fx ok

Expected output is ``ok``.

Verify go-import metadata:

.. code-block:: bash

   curl --fail --silent --show-error \
     "http://${INGRESS_HOST}/yaml.v2?go-get=1" \
     --resolve ${INGRESS_HOST}:80:127.0.0.1 | grep go-import

Expected output contains a ``go-import`` meta tag.

Step 6: test runtime configuration
----------------------------------

Update charm config and confirm it applies without rebuild:

.. code-block:: bash

   juju config gopkg-charmed hostname=staging.example.com

.. SPREAD
   juju wait-for application gopkg-charmed \
     --query='status=="active"' --timeout=15m
.. SPREAD END

Then query again:

.. code-block:: bash

   curl --fail --silent --show-error \
     "http://${INGRESS_HOST}/yaml.v2?go-get=1" \
     --resolve ${INGRESS_HOST}:80:127.0.0.1 | grep staging.example.com

You should see output reflecting the new hostname value.

If the change is not immediately visible, wait for ``juju status`` to return
``active`` and run the request again.

What to read next
-----------------

- :ref:`Deploy locally with MicroK8s and Juju <deploy-locally-with-microk8s>`
- :ref:`Configure hostname and verify go-import metadata <configure-hostname-and-check-go-import>`
- :ref:`Troubleshoot deployment <troubleshoot-deployment>`

.. _deploy-locally-with-microk8s:

.. meta::
   :description: Build and deploy the gopkg-charmed rock and charm locally with MicroK8s, Juju, and ingress.

Deploy locally with MicroK8s and Juju
=====================================

A local deployment verifies that the rock and charm work together before they
reach a shared environment. Build the artifacts, deploy them to MicroK8s with
Juju, and expose the service through ingress.

For first-time environment preparation, start with
:ref:`set-up-a-local-linux-environment`.

Prerequisites
-------------

Make sure your Linux environment has these tools installed:

- MicroK8s
- Juju
- Rockcraft
- Charmcraft
- LXD initialized once via ``lxd init --auto``

Deployment steps
----------------

1. Enable required MicroK8s add-ons.

.. code-block:: bash

   sudo microk8s enable dns hostpath-storage registry ingress
   microk8s status --wait-ready

2. Bootstrap Juju and create a model.

.. code-block:: bash

   juju bootstrap microk8s dev

.. code-block:: bash

   juju add-model gopkg-charmed

3. Pin model architecture to the machine architecture.

.. code-block:: bash

   juju set-model-constraints arch=$(dpkg --print-architecture)

4. Build and push rock image.

.. code-block:: bash

   cd ~/gopkg-charm/app
   ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true rockcraft pack
   rockcraft.skopeo copy --insecure-policy --dest-tls-verify=false --dest-no-creds \
     oci-archive:gopkg_0.1_$(dpkg --print-architecture).rock \
     docker://localhost:32000/gopkg:0.1

5. Build charm.

.. code-block:: bash

   cd ~/gopkg-charm/app/charm
   CHARMCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true charmcraft pack

6. Deploy app and ingress.

.. code-block:: bash

   cd ~/gopkg-charm/app/charm
   juju deploy ./gopkg-charmed_*.charm gopkg-charmed \
     --resource app-image=localhost:32000/gopkg:0.1
   juju deploy nginx-ingress-integrator --channel=latest/stable --trust
   juju integrate nginx-ingress-integrator gopkg-charmed
   juju config nginx-ingress-integrator \
     service-hostname=gopkg.example.com \
     path-routes=/ \
     rewrite-enabled=false

7. Wait for active status.

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

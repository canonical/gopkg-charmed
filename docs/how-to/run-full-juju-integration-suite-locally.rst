.. _run-full-juju-integration-suite-locally:

Run the full Juju integration suite locally
===========================================

This guide runs the full charm integration suite locally on both ``amd64`` and
``arm64``.

If you are on macOS, run these steps inside a Linux VM (for example Multipass).

Prerequisites
-------------

You need these tools inside Linux:

- ``microk8s``
- ``juju``
- ``rockcraft``
- ``charmcraft``
- ``tox``

Quick architecture check:

.. code-block:: bash

   dpkg --print-architecture

Expected: ``amd64`` or ``arm64``.

Recommended one-command path
----------------------------

From the repository root:

.. code-block:: bash

   app/charm/tests/integration/run_full_local_suite.sh

This script will:

1. verify Linux and required commands
2. detect architecture (``amd64`` or ``arm64``)
3. ensure MicroK8s readiness and required add-ons
4. ensure Juju controller availability
5. build and push the architecture-matching rock
6. build charm
7. run ``tox -e integration`` with ``CHARM_FILE`` and ``APP_IMAGE``

Manual path (if you need fine-grained control)
-----------------------------------------------

.. code-block:: bash

   sudo microk8s enable hostpath-storage registry ingress
   microk8s status --wait-ready
   juju bootstrap microk8s dev

   cd app
   ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true rockcraft pack
   rockcraft.skopeo copy --insecure-policy --dest-tls-verify=false \
     oci-archive:gopkg_0.1_$(dpkg --print-architecture).rock \
     docker://localhost:32000/gopkg:0.1

   cd charm
   CHARMCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true charmcraft pack
   CHARM_FILE=$(ls -1 gopkg-charmed_*.charm | head -n1)
   CHARM_FILE="$CHARM_FILE" APP_IMAGE=localhost:32000/gopkg:0.1 tox -e integration

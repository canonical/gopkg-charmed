.. _run-full-juju-integration-suite-locally:

Run the full Juju integration suite locally
===========================================

This guide runs the full charm integration suite locally on Linux ``amd64`` and
Linux ``arm64``.

If you are on macOS, run these steps inside a Linux VM (for example Multipass).
For a complete first-time setup path, see :ref:`set-up-a-local-linux-environment`.

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

   cd ~/gopkg-charm
   app/charm/tests/integration/run_full_local_suite.sh

This script will:

1. verify Linux and required commands
2. detect architecture (``amd64`` or ``arm64``)
3. ensure MicroK8s readiness and required add-ons
4. ensure Juju controller availability
5. build and push the architecture-matching rock
6. build charm
7. run the integration tox environment with ``CHARM_FILE`` and ``APP_IMAGE``

What this guide validates
-------------------------

This is an end-to-end deployment validation path. It verifies that:

- the packed rock and charm artifacts can be built for your architecture
- Juju can deploy the charm with the local image resource
- integration tests can reach active status and validate service behavior

If this command fails on macOS directly, that is expected: the suite requires
Linux tools and a Linux Juju/MicroK8s environment.

If ``rockcraft pack`` fails with a ``PermissionError`` under
``app/charm/.tox/.../python3.12``, remove local virtualenv artifacts and retry.
See :ref:`set-up-a-local-linux-environment` for the cleanup command.

Manual path (if you need fine-grained control)
-----------------------------------------------

.. code-block:: bash

   cd ~/gopkg-charm
   sudo microk8s enable hostpath-storage registry ingress
   microk8s status --wait-ready
   microk8s kubectl rollout status deployment/registry \
       -n container-registry --timeout=5m
   curl --fail http://127.0.0.1:32000/v2/
   juju bootstrap microk8s dev

   cd ~/gopkg-charm/app
   ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true rockcraft pack
   rockcraft.skopeo copy --insecure-policy --dest-tls-verify=false \
     oci-archive:gopkg_0.1_$(dpkg --print-architecture).rock \
     docker://localhost:32000/gopkg:0.1

   cd ~/gopkg-charm/app/charm
   CHARMCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true charmcraft pack
   CHARM_FILE=$(ls -1 gopkg-charmed_*.charm | head -n1)
    CHARM_FILE="$CHARM_FILE" APP_IMAGE=localhost:32000/gopkg:0.1 \
       tox --workdir ~/.cache/gopkg-charm-tox -e integration

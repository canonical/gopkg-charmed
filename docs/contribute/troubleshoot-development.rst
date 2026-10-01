.. _troubleshoot-development:

.. meta::
   :description: Diagnose and fix common registry, rock build, and tox failures when building gopkg-k8s from source.

Troubleshoot the development environment
========================================

Before troubleshooting, confirm the tools as the last step of
:ref:`set-up-a-development-environment` does. Each entry below names the
symptom, the usual cause, and the fix. For failures of a running deployment,
see :ref:`troubleshoot-deployment`.

Local image registry refuses connections
----------------------------------------

**Symptom:** ``curl http://localhost:32000/v2/`` or ``rockcraft.skopeo copy``
reports ``connection refused``.

**Cause:** the registry add-on is disabled or its deployment is not ready yet.

**Fix:** enable the add-ons and wait for the registry (with strict MicroK8s,
enabling add-ons requires ``sudo`` even after joining the group):

.. code-block:: bash

   microk8s status --wait-ready
   sudo microk8s enable dns hostpath-storage registry ingress
   microk8s kubectl rollout status deployment/registry \
     -n container-registry --timeout=15m
   curl --fail --silent --show-error --retry 30 --retry-delay 2 \
     --retry-all-errors http://127.0.0.1:32000/v2/

The last command returns ``{}``. Retry the image push; the rock does not need
to be rebuilt.

Rock or charm build fails on architecture
-----------------------------------------

**Symptom:** the build error says no build matches the current execution
environment.

**Cause:** the ``platforms`` entries in the rock or charm recipe do not include
the machine's architecture.

**Fix:** check the architecture and make sure the recipes list it:

.. code-block:: bash

   dpkg --print-architecture
   grep -A3 '^platforms:' app/rockcraft.yaml app/charm/charmcraft.yaml

Rock build fails on a Python file from another OS
-------------------------------------------------

**Symptom:** ``rockcraft pack`` reports ``PermissionError`` for a path such as
``app/charm/.tox/unit/bin/python3.12``.

**Cause:** Python environment files created on another operating system entered
the rock build context through a mounted checkout.

**Fix:** remove them and rebuild; recreate the environments with ``tox`` inside
the Linux environment afterwards:

.. code-block:: bash

   cd ~/gopkg-charm
   rm -rf app/charm/.tox app/charm/.venv

Tox fails to create an environment in a mounted checkout
--------------------------------------------------------

**Symptom:** ``tox`` reports ``PermissionError`` while creating ``app/charm/.tox``
in a repository mounted from the host.

**Cause:** the mounted filesystem does not support the permissions the virtual
environment needs.

**Fix:** keep the environment on the VM filesystem instead:

.. code-block:: bash

   cd ~/gopkg-charm/app/charm
   tox --workdir ~/.cache/gopkg-charm-tox -e integration

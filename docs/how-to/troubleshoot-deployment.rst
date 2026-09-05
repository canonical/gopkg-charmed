.. _troubleshoot-deployment:

.. meta::
   :description: Diagnose and fix common MicroK8s, Juju, rock, charm, ingress, architecture, and registry deployment failures.

Troubleshoot deployment issues
==============================

Before troubleshooting, verify baseline environment setup with
:ref:`set-up-a-local-linux-environment`.

Juju cannot access MicroK8s
---------------------------

Symptom:

- ``juju bootstrap microk8s dev`` reports
   ``Insufficient permissions to access MicroK8s``.

Cause:

- the current shell does not have the new ``snap_microk8s`` group membership.

Fix:

.. code-block:: bash

    sudo usermod -a -G snap_microk8s "$USER"
    newgrp snap_microk8s
    id -nG | grep -qw snap_microk8s

You can instead exit the VM and run ``multipass shell charm-dev`` again. Do
not bootstrap Juju until the group check succeeds.

Local image registry refuses connections
-----------------------------------------

Symptom:

- ``curl http://localhost:32000/v2/`` or ``rockcraft.skopeo copy`` reports
   ``connection refused``.

Cause:

- the registry add-on is disabled or its deployment is not ready. With strict
   MicroK8s, enabling add-ons requires ``sudo`` even after joining the
   ``snap_microk8s`` group.

Fix:

.. code-block:: bash

    sudo microk8s enable hostpath-storage registry ingress
    microk8s kubectl rollout status deployment/registry \
       -n container-registry --timeout=5m
    curl --fail http://127.0.0.1:32000/v2/

The last command should return ``{}``. You can then retry the image push; the
rock does not need to be rebuilt.

Pods stay Pending
-----------------

Symptom:

- Juju unit does not become active.
- Kubernetes pod remains ``Pending``.

Check:

.. code-block:: bash

   microk8s kubectl describe pod -n gopkg-charmed gopkg-charmed-0

If you see an architecture mismatch, set model constraints before deploying:

.. code-block:: bash

   juju set-model-constraints arch=$(dpkg --print-architecture)

Ingress returns unexpected redirects
------------------------------------

Symptom:

- every path appears to redirect unexpectedly

Fix:

.. code-block:: bash

   juju config nginx-ingress-integrator rewrite-enabled=false

Ingress relation blocked on hostname
------------------------------------

Symptom:

- ingress integrator reports ``blocked`` due to missing hostname

Fix:

.. code-block:: bash

   export INGRESS_HOST=gopkg.example.com
   juju config nginx-ingress-integrator service-hostname=${INGRESS_HOST}

Rock or charm build fails on architecture
-----------------------------------------

Symptom:

- build error indicates unsupported execution environment

Fix:

1. Check local architecture:

.. code-block:: bash

   dpkg --print-architecture

2. Ensure platform entries in charm and rock config include that architecture.

Rock build fails on a Python file from another OS
-------------------------------------------------

Symptom:

- ``rockcraft pack`` reports ``PermissionError`` for a path such as
   ``app/charm/.tox/unit/bin/python3.12``.

Cause:

- local Python environment files created on another OS entered the rock build
   context.

Fix:

.. code-block:: bash

   cd ~/gopkg-charm
   rm -rf app/charm/.tox app/charm/.venv

Do not copy Python environments between operating systems. Recreate them with
``tox`` inside the Linux environment after removing the incompatible files.

Tox fails to create an environment in a mounted checkout
---------------------------------------------------------

Symptom:

- ``tox`` reports ``PermissionError`` while creating ``app/charm/.tox`` in a
   repository mounted from macOS.

Fix:

.. code-block:: bash

   cd ~/gopkg-charm/app/charm
   tox --workdir ~/.cache/gopkg-charm-tox -e integration

This creates the virtual environment on the VM filesystem instead of the
mounted host filesystem.

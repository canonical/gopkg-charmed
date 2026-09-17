.. _troubleshoot-deployment:

Troubleshoot deployment issues
==============================

Pods stay Pending
-----------------

Symptom:

- Juju unit does not become active.
- Kubernetes pod remains ``Pending``.

Check:

.. code-block:: bash

   kubectl describe pod -n gopkg-charmed gopkg-charmed-0

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

   juju config nginx-ingress-integrator service-hostname=gopkg.example.com

Rock or charm build fails on architecture
-----------------------------------------

Symptom:

- build error indicates unsupported execution environment

Fix:

1. Check local architecture:

.. code-block:: bash

   dpkg --print-architecture

2. Ensure platform entries in charm and rock config include that architecture.

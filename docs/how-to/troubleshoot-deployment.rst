.. _troubleshoot-deployment:

.. meta::
   :description: Diagnose and fix common MicroK8s, Juju, rock, charm, ingress, architecture, and registry deployment failures.

How to troubleshoot deployment issues
=====================================

Before troubleshooting, verify the baseline environment with
:ref:`set-up-a-local-linux-environment`. Each entry below names the symptom,
the usual cause, and the fix.

Juju cannot access MicroK8s
---------------------------

Symptom: ``juju bootstrap microk8s dev`` reports ``Insufficient permissions
to access MicroK8s``.

Cause: the current shell started before your user joined the
``snap_microk8s`` group, so the membership is not active in it.

Fix: add the membership if it is missing, then log out and back in. In a
Multipass VM, run ``multipass shell charm-dev`` again:

.. code-block:: bash

   id -nG | grep -qw snap_microk8s || sudo adduser $USER snap_microk8s

Do not bootstrap Juju until ``id -nG | grep -qw snap_microk8s`` succeeds in
the new session. In an interactive shell, ``newgrp snap_microk8s`` also
applies the membership, but it opens a new shell: do not paste further
commands after it.

Local image registry refuses connections
----------------------------------------

Symptom: ``curl http://localhost:32000/v2/`` or ``rockcraft.skopeo copy``
reports ``connection refused``.

Cause: the registry add-on is disabled or its deployment is not ready yet.

Fix: enable the add-ons and wait for the registry (with strict MicroK8s,
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

Pods stay Pending
-----------------

Symptom: the Juju unit does not become active and the Kubernetes pod remains
``Pending``.

Cause: either the model has no architecture constraint, so Juju schedules
for AMD64 on an ARM64 node, or the machine has too little memory. 4 GB of
RAM can leave the Juju controller without enough capacity to schedule the
charm workloads.

Fix: check the pod's events for the exact reason:

.. code-block:: bash

   microk8s kubectl describe pod -n gopkg-charmed gopkg-charmed-0

For an architecture mismatch, set the constraint before deploying:

.. code-block:: bash

   juju set-model-constraints arch=$(dpkg --print-architecture)

For insufficient memory, give the machine at least 8 GB of RAM. In a
Multipass VM: ``multipass stop charm-dev``, then
``multipass set local.charm-dev.memory=8G``, then ``multipass start
charm-dev``.

Ingress returns 404 for every request
-------------------------------------

Symptom: requests through ingress return ``404`` from the controller although
the application is active.

Cause: the request hostname does not match ``service-hostname`` exactly, or
``path-routes`` does not include the requested path.

Fix: align the request with the rule. With curl, include the matching
``--resolve`` entry:

.. code-block:: bash

   juju config nginx-ingress-integrator service-hostname path-routes
   curl --fail --silent --show-error http://gopkg.example.com/health-check \
     --resolve gopkg.example.com:80:127.0.0.1

Ingress returns unexpected redirects
------------------------------------

Symptom: every path redirects or the backend sees the wrong path.

Cause: path rewriting is enabled, so the controller changes the path before
forwarding it and the workload never receives the package path.

Fix:

.. code-block:: bash

   juju config nginx-ingress-integrator rewrite-enabled=false

Ingress relation blocked on hostname
------------------------------------

Symptom: ``nginx-ingress-integrator`` reports ``blocked`` because
``service-hostname`` is not set.

Cause: the integrator has no hostname to route, or the integration with
``gopkg-charmed`` is missing.

Fix: set the hostname and confirm the integration exists:

.. code-block:: bash

   juju config nginx-ingress-integrator service-hostname=gopkg.example.com
   juju status --relations

Requests reach the wrong application
------------------------------------

Symptom: a request for the ``gopkg-charmed`` hostname is answered by another
application.

Cause: another Ingress resource claims the same hostname and path, or the
cluster runs several ingress controllers and the rule is implemented by the
wrong one.

Fix: inspect all Ingress resources for duplicate rules. If the cluster has
several controllers, set the integrator's ``ingress-class`` to the class that
should implement this route:

.. code-block:: bash

   microk8s kubectl get ingress --all-namespaces
   juju config nginx-ingress-integrator ingress-class=public

Ingress returns 502 or 503
--------------------------

Symptom: requests through ingress return ``502`` or ``503``.

Cause: the routing rule exists before the backend is ready, or the workload
is restarting after a configuration change.

Fix: wait for both applications to be active, then retry:

.. code-block:: bash

   juju wait-for application gopkg-charmed \
     --query='status=="active"' --timeout=15m
   juju wait-for application nginx-ingress-integrator \
     --query='status=="active"' --timeout=15m

If the status is active and the error persists, check the application pods,
the Service endpoints, and the ingress-controller logs.

The hostname does not resolve
-----------------------------

Symptom: ``curl`` reports ``Could not resolve host``.

Cause: the hostname has no DNS record. The documentation hostname
``gopkg.example.com`` never resolves on its own.

Fix: for local testing, pin the hostname with ``--resolve`` and the
controller's reachable address, as the guides do. For production, create or
correct the DNS record as described in :ref:`configure-ingress`.

HTTPS reports a certificate error
---------------------------------

Symptom: an HTTPS request fails with a certificate error.

Cause: the certificate does not cover the requested hostname, the TLS secret
is in the wrong namespace, or ``tls-secret-name`` does not match the secret.

Fix: confirm all three. The secret must be in the model's namespace:

.. code-block:: bash

   microk8s kubectl -n gopkg-charmed get secret
   juju config nginx-ingress-integrator tls-secret-name

Rock or charm build fails on architecture
-----------------------------------------

Symptom: the build error says no build matches the current execution
environment.

Cause: the ``platforms`` entries in the rock or charm recipe do not include
the machine's architecture.

Fix: check the architecture and make sure the recipes list it:

.. code-block:: bash

   dpkg --print-architecture
   grep -A3 '^platforms:' app/rockcraft.yaml app/charm/charmcraft.yaml

Rock build fails on a Python file from another OS
-------------------------------------------------

Symptom: ``rockcraft pack`` reports ``PermissionError`` for a path such as
``app/charm/.tox/unit/bin/python3.12``.

Cause: Python environment files created on another operating system entered
the rock build context through a mounted checkout.

Fix: remove them and rebuild; recreate the environments with ``tox`` inside
the Linux environment afterwards:

.. code-block:: bash

   cd ~/gopkg-charm
   rm -rf app/charm/.tox app/charm/.venv

Tox fails to create an environment in a mounted checkout
--------------------------------------------------------

Symptom: ``tox`` reports ``PermissionError`` while creating ``app/charm/.tox``
in a repository mounted from the host.

Cause: the mounted filesystem does not support the permissions the virtual
environment needs.

Fix: keep the environment on the VM filesystem instead:

.. code-block:: bash

   cd ~/gopkg-charm/app/charm
   tox --workdir ~/.cache/gopkg-charm-tox -e integration

For every ingress integrator setting, see the `NGINX ingress integrator
configuration reference
<https://charmhub.io/nginx-ingress-integrator/configurations>`_.

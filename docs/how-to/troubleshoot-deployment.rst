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

**Symptom:** ``juju bootstrap microk8s dev`` reports ``Insufficient permissions
to access MicroK8s``.

**Cause:** the current shell started before your user joined the
``snap_microk8s`` group, so the membership is not active in it.

**Fix:** add the membership if it is missing, then log out and back in. In a
Multipass VM, run ``multipass shell charm-dev`` again:

.. code-block:: bash

   id -nG | grep -qw snap_microk8s || sudo adduser $USER snap_microk8s

Do not bootstrap Juju until ``id -nG | grep -qw snap_microk8s`` succeeds in
the new session. In an interactive shell, ``newgrp snap_microk8s`` applies
the membership without logging out. It starts a new shell, so any commands
pasted together with it run in the original shell, before the membership
applies.

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

Pods stay Pending
-----------------

**Symptom:** ``juju status`` never reports the unit as ``active``, and
``microk8s kubectl get pods -n gopkg-k8s`` shows its pod as ``Pending``.

**Cause:** either the model has no architecture constraint, so Juju schedules
for AMD64 on an ARM64 node, or the machine has too little memory. 4 GB of
RAM can leave the Juju controller without enough capacity to schedule the
charm workloads.

**Fix:** check the pod's events for the exact reason:

.. code-block:: bash

   microk8s kubectl describe pod -n gopkg-k8s gopkg-k8s-0

For an architecture mismatch, set the constraint before deploying:

.. code-block:: bash

   juju set-model-constraints arch=$(dpkg --print-architecture)

For insufficient memory, give the machine at least 8 GB of RAM. In a
Multipass VM: ``multipass stop charm-dev``, then
``multipass set local.charm-dev.memory=8G``, then ``multipass start
charm-dev``.

Ingress returns 404 for every request
-------------------------------------

**Symptom:** requests through ingress return ``404`` from the controller although
the application is active.

**Cause:** the request hostname does not match ``service-hostname`` exactly, or
``path-routes`` does not include the requested path.

**Fix:** align the request with the rule. With curl, include the matching
``--resolve`` entry:

.. code-block:: bash

   juju config nginx-ingress-integrator service-hostname
   juju config nginx-ingress-integrator path-routes
   curl --fail --silent --show-error http://gopkg.example.com/health-check \
     --resolve gopkg.example.com:80:127.0.0.1

Ingress returns unexpected redirects
------------------------------------

**Symptom:** every path redirects or the backend sees the wrong path.

**Cause:** path rewriting is enabled, so the controller changes the path before
forwarding it and the workload never receives the package path.

**Fix:** Disable path rewriting using the `rewrite-enabled` configuration:

.. code-block:: bash

   juju config nginx-ingress-integrator rewrite-enabled=false

Ingress relation blocked on hostname
------------------------------------

**Symptom:** ``nginx-ingress-integrator`` reports ``blocked`` because
``service-hostname`` is not set.

**Cause:** the integrator has no hostname to route, or the integration with
``gopkg-k8s`` is missing.

**Fix:** set the hostname and confirm the integration exists:

.. code-block:: bash

   juju config nginx-ingress-integrator service-hostname=gopkg.example.com
   juju status --relations

Requests reach the wrong application
------------------------------------

**Symptom:** a request for the ``gopkg-k8s`` hostname is answered by another
application.

**Cause:** another Ingress resource claims the same hostname and path, or the
cluster runs several ingress controllers and the rule is implemented by the
wrong one.

**Fix:** inspect all Ingress resources for duplicate rules. If the cluster has
several controllers, set the integrator's ``ingress-class`` to the class that
should implement this route:

.. code-block:: bash

   microk8s kubectl get ingress --all-namespaces
   juju config nginx-ingress-integrator ingress-class=public

Ingress returns 502 or 503
--------------------------

**Symptom:** requests through ingress return ``502`` or ``503``.

**Cause:** the routing rule exists before the backend is ready, or the workload
is restarting after a configuration change.

**Fix:** wait for both applications to be active, then retry:

.. code-block:: bash

   juju wait-for application gopkg-k8s \
     --query='status=="active"' --timeout=15m
   juju wait-for application nginx-ingress-integrator \
     --query='status=="active"' --timeout=15m

If the status is active and the error persists, check the application pods,
the Service endpoints, and the ingress-controller logs.

The hostname does not resolve
-----------------------------

**Symptom:** ``curl`` reports ``Could not resolve host``.

**Cause:** the hostname has no DNS record. The documentation hostname
``gopkg.example.com`` never resolves on its own.

**Fix:** for local testing, pin the hostname with ``--resolve`` and the
controller's reachable address, as the guides do. For production, create or
correct the DNS record as described in :ref:`configure-ingress`.

HTTPS reports a certificate error
---------------------------------

**Symptom:** an HTTPS request fails with a certificate error.

**Cause:** the certificate does not cover the requested hostname, the TLS secret
is in the wrong namespace, or ``tls-secret-name`` does not match the secret.

**Fix:** confirm all three. The secret must be in the model's namespace:

.. code-block:: bash

   microk8s kubectl -n gopkg-k8s get secret
   juju config nginx-ingress-integrator tls-secret-name

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

.. _cos-charm-blocked-patch-unauthorized:

COS charm blocked on a Kubernetes patch
---------------------------------------

**Symptom:** after :ref:`integrate-with-cos`, ``grafana-k8s``,
``prometheus-k8s``, or ``loki-k8s`` stays ``blocked`` with ``Kubernetes
resources patch failed: Unauthorized`` while the others are ``active``.

**Cause:** shortly after it first reports active, each COS charm patches its
own StatefulSet to set resource limits. Occasionally the Kubernetes API
rejects the service-account token the unit presents for that patch. This is
a race between Juju and the charm, not a problem with ``gopkg-k8s`` or the
integration, and the charm does not retry on its own, so the unit stays
blocked indefinitely.

**Fix:** remove the blocked application and deploy it again, then restore
its integration. For ``grafana-k8s``:

.. code-block:: bash

   juju remove-application grafana-k8s --destroy-storage --force --no-prompt
   while juju status --format=json | grep -q '"grafana-k8s"'; do sleep 5; done
   juju deploy grafana-k8s --channel=2/stable --trust
   juju integrate gopkg-k8s:grafana-dashboard grafana-k8s:grafana-dashboard

For ``prometheus-k8s`` or ``loki-k8s``, substitute the application name and
its ``juju integrate`` line from :ref:`integrate-with-cos`. The loop waits
until Juju has finished removing the old application, because a new one
cannot use the name before then. One redeployment is normally enough; the
charm's integration tests use the same recovery.

.. _prometheus-does-not-scrape:

Prometheus does not report the service as up
--------------------------------------------

**Symptom:** a wait loop in :ref:`integrate-with-cos` ends with ``Prometheus
has not scraped gopkg-k8s successfully`` or ``Prometheus has no healthy
target on port 9102``.

**Cause:** one of three things: ``PROMETHEUS_IP`` is empty, so ``curl`` never
reached Prometheus; Prometheus has no scrape target for ``gopkg-k8s``,
because the ``metrics-endpoint`` integration is missing or Prometheus has
not processed it yet; or the target exists but the scrape fails, which
Prometheus records as the target's ``lastError``.

**Fix:** find out which, in that order:

.. code-block:: bash

   echo "${PROMETHEUS_IP}"
   juju status --relations prometheus-k8s gopkg-k8s
   curl --silent --show-error \
     "http://${PROMETHEUS_IP}:9090/api/v1/targets?state=active" \
     | grep --only-matching \
       '"scrapeUrl":"[^"]*"\|"lastError":"\(\\.\|[^"\\]\)*"\|"health":"[^"]*"'

If ``echo`` prints nothing, the Service lookup failed: run the ``export``
line from the guide again and check that ``microk8s kubectl`` works. If
``juju status`` shows ``prometheus-k8s`` as ``blocked``, see
:ref:`cos-charm-blocked-patch-unauthorized`; if the ``metrics-endpoint``
integration is not listed, run its ``juju integrate`` line again. Otherwise
the last command prints the scrape URL, last error, and health of every
target. A ``gopkg-k8s`` target whose ``lastError`` is not empty names the
reason; check it against the service directly, with the unit address from
``juju status`` and the port from the scrape URL:

.. code-block:: bash

   curl --fail --silent --show-error http://<unit-address>:<port>/metrics | head -3

The output starts with ``# HELP`` lines. If there is no ``gopkg-k8s`` target
at all although the integration is listed, Prometheus has not reloaded its
configuration yet; wait a minute and query the targets again.

If the direct request is refused on the ``metrics-port`` port, or answers
``404`` on the application port, the running image does not serve metrics:
it was built from a checkout that predates ``app/observability.go``, or the
pod is still running an older image that was cached under the same tag,
because Kubernetes does not pull an image again for a tag it already has.
Rebuild the rock from the current checkout, push it under a new tag, and
attach that tag as the resource, which replaces the pod:

.. code-block:: bash

   cd ~/gopkg-charm/app
   rm -f gopkg_0.1_$(dpkg --print-architecture).rock
   ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true rockcraft pack
   rockcraft.skopeo copy --insecure-policy --dest-tls-verify=false --dest-no-creds \
     oci-archive:gopkg_0.1_$(dpkg --print-architecture).rock \
     docker://localhost:32000/gopkg:0.1-1
   juju attach-resource gopkg-k8s app-image=localhost:32000/gopkg:0.1-1
   microk8s kubectl -n gopkg-k8s rollout status statefulset/gopkg-k8s --timeout=15m

The application stays ``active`` while its pod is replaced, so the last
command, not ``juju status``, tells you when the new image is running. Then
repeat the wait loop from the guide.

For every ingress integrator setting, see the `NGINX ingress integrator
configuration reference
<https://charmhub.io/nginx-ingress-integrator/configurations>`_.

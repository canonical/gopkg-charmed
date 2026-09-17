.. _deploy-and-verify-on-kubernetes:

.. meta::
   :description: Build the gopkg-charmed rock and charm, deploy them on Kubernetes with Juju, and verify ingress and go-import metadata.

Deploy and verify gopkg-charmed on Kubernetes
=============================================

An end-to-end deployment shows how the Go service, rock, charm, Juju, and
ingress work together. Build the artifacts, deploy them on Kubernetes, and
verify the service on AMD64 or ARM64.

What you'll do
--------------

1. Build and publish the rock image
2. Build the charm
3. Deploy to a new model
4. Verify the deployment
5. Update the hostname
6. Clean up

Along the way, you will have a running ``gopkg-charmed`` application in a
Juju model, an ingress relation for external routing, and a verified
health endpoint and go-import metadata endpoint.

Prerequisites
-------------

You need a workstation with AMD64 or ARM64 architecture and the environment
from :ref:`set-up-a-local-linux-environment`. After following that guide,
you'll have an Ubuntu environment with the repository and the required tools,
and your user will belong to the MicroK8s group.

Enter the repository root before continuing:

.. code-block:: bash

   cd ~/gopkg-charm

Confirm that MicroK8s access and the local registry are still ready. These
repeat the setup guide's final checks on purpose: a shell opened before you
joined the group, or a restarted machine whose registry is still starting,
fails here rather than in the middle of the image push:

.. code-block:: bash

   id -nG | grep -qw snap_microk8s
   microk8s status --wait-ready
   microk8s kubectl rollout status deployment/registry \
     -n container-registry --timeout=15m
   curl --fail --silent --show-error --retry 30 --retry-delay 2 \
     --retry-all-errors http://127.0.0.1:32000/v2/

The group check prints nothing, the status command reports ``microk8s is
running`` with the add-ons listed, the third command ends with
``deployment "registry" successfully rolled out``, and the registry check
prints ``{}``. If the registry check cannot connect, see
:ref:`troubleshoot-deployment`.

Bootstrap a Juju controller on the MicroK8s cloud. The controller is the
management service that every ``juju`` command talks to:

.. code-block:: bash

   juju bootstrap microk8s dev

Build and publish the rock image
--------------------------------

The rock is the container image that carries the compiled ``gopkg.in``
service. Its recipe, ``app/rockcraft.yaml``, uses Rockcraft's Go framework
extension, which builds the Go module and sets up the runtime. The extension
is still marked experimental, so the environment variable opts in to it.
From the repository root, build the rock:

.. SPREAD SKIP

.. code-block:: bash

   cd ~/gopkg-charm/app
   ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true rockcraft pack

.. SPREAD SKIP END

.. SPREAD
   cd ~/gopkg-charm/app
   for attempt in 1 2 3 4 5; do
     ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true rockcraft pack && break
     [ "${attempt}" -lt 5 ] || exit 1
     sleep 60
   done
.. SPREAD END

The build runs inside an LXD instance and fetches packages from the Ubuntu
archive, so the first build takes several minutes. It produces
``gopkg_0.1_<architecture>.rock`` in ``app/``.

Kubernetes pulls images from a registry, not from files, so push the rock
to the local registry that the MicroK8s ``registry`` add-on runs on port
32000. ``rockcraft.skopeo`` is the copy of ``skopeo`` that ships inside the
Rockcraft snap; the flags allow the plain-HTTP, unauthenticated local
registry:

.. code-block:: bash

   rockcraft.skopeo copy --insecure-policy --dest-tls-verify=false --dest-no-creds \
     oci-archive:gopkg_0.1_$(dpkg --print-architecture).rock \
     docker://localhost:32000/gopkg:0.1

Verify that the registry now holds the image:

.. code-block:: bash

   curl --fail --silent --show-error \
     http://localhost:32000/v2/gopkg/tags/list | grep -F '"0.1"'

The output contains ``"0.1"``. If the push did not happen, the registry has
no tag list for ``gopkg``, ``grep`` finds nothing, and the command exits with
a failure.

Build the charm
---------------

The rock is the workload, and the charm is the operator that tells Juju how to
run it. Its definition lives in ``app/charm`` and uses Charmcraft's Go
framework extension, the counterpart of the Rockcraft extension you used
above, which is why the same kind of environment variable is needed.
Enter the charm directory and pack the charm:

.. SPREAD SKIP

.. code-block:: bash

   cd ~/gopkg-charm/app/charm
   CHARMCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true charmcraft pack

.. SPREAD SKIP END

.. SPREAD
   cd ~/gopkg-charm/app/charm
   for attempt in 1 2 3 4 5; do
     CHARMCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true charmcraft pack && break
     [ "${attempt}" -lt 5 ] || exit 1
     sleep 60
   done
.. SPREAD END

Confirm that the charm was packed:

.. code-block:: bash

   ls -1 gopkg-charmed_$(dpkg --print-architecture).charm

The command prints the name of the packed charm, such as
``gopkg-charmed_amd64.charm``.

Deploy to a new model
---------------------

A Juju model is a workspace that holds a set of applications; on Kubernetes,
each model is a namespace. Create one for this deployment: 

.. code-block:: bash

   juju add-model gopkg-charmed
   juju set-model-constraints arch=$(dpkg --print-architecture)

The constraint
tells Juju to schedule the deployment's pods on your machine's architecture,
which is necessary because the rock you built only works for that
architecture.

Deploy the charm you built. It is a local file rather than a charm from
Charmhub, and the ``app-image`` resource points it at the rock in the local
registry:

.. code-block:: bash

   cd ~/gopkg-charm/app/charm
   juju deploy ./gopkg-charmed_$(dpkg --print-architecture).charm gopkg-charmed \
     --resource app-image=localhost:32000/gopkg:0.1

On its own, the service is reachable only inside the cluster. To publish it
under a hostname, deploy the NGINX ingress integrator from Charmhub. That
charm does not serve traffic itself: it configures the ingress controller
that the MicroK8s ``ingress`` add-on runs, and ``--trust`` grants it the
Kubernetes permissions it needs to create ingress resources:

.. code-block:: bash

   juju deploy nginx-ingress-integrator --channel=latest/stable --trust

Integrate the two applications:

.. code-block:: bash

   juju integrate nginx-ingress-integrator gopkg-charmed

Over the relation, ``gopkg-charmed`` tells
the integrator the name and port of its Kubernetes service, and the
integrator writes the routing rule.

Set an ingress hostname and keep it in the ``INGRESS_HOST`` variable, which
the remaining commands reuse:

.. code-block:: bash

   export INGRESS_HOST=gopkg.example.com

``example.com`` is reserved for documentation, so ``gopkg.example.com``
never resolves to a real machine and needs no DNS record for this tutorial.
Later, you will make ``curl`` pin the name to ``127.0.0.1`` with
``--resolve`` so requests reach the ingress controller on your machine.

Configure the integrator to route ``INGRESS_HOST`` to the service:

.. code-block:: bash

   juju config nginx-ingress-integrator \
      service-hostname=${INGRESS_HOST} \
     path-routes=/ \
     rewrite-enabled=false

``service-hostname`` is the hostname the routing rule matches, so only
requests for ``INGRESS_HOST`` reach the service. ``path-routes=/`` forwards
every path under that hostname, which the service needs because package
paths such as ``/yaml.v2`` are the whole point of it. ``rewrite-enabled=false``
tells the controller to pass paths through unchanged instead of rewriting
them to ``/``, which would turn every package request into a request for the
front page. :ref:`configure-ingress` covers these settings in more depth.

.. SPREAD
   juju wait-for application gopkg-charmed \
     --query='status=="active"' --timeout=15m
   juju wait-for application nginx-ingress-integrator \
     --query='status=="active"' --timeout=15m
.. SPREAD END

Verify the deployment
---------------------

Check that both applications are active and that the integration exists:

.. code-block:: bash

   juju status --relations

The output looks like this once the deployment has settled; if a status is
still ``waiting`` or ``maintenance``, run the command again after a minute:

.. SPREAD SKIP

.. code-block:: text

   Model          Controller  Cloud/Region        Version  SLA          Timestamp
   gopkg-charmed  dev         microk8s/localhost  3.6.28   unsupported  22:13:30Z

   App                       Version  Status  Scale  Charm                     Channel        Rev  Address         Exposed  Message
   gopkg-charmed                      active      1  gopkg-charmed                              0  10.152.183.31   no
   nginx-ingress-integrator  24.2.0   active      1  nginx-ingress-integrator  latest/stable  203  10.152.183.208  no

   Unit                         Workload  Agent  Address      Ports  Message
   gopkg-charmed/0*             active    idle   10.1.58.140
   nginx-ingress-integrator/0*  active    idle   10.1.58.141

   Integration provider                  Requirer                              Interface       Type     Message
   gopkg-charmed:secret-storage          gopkg-charmed:secret-storage          secret-storage  peer
   nginx-ingress-integrator:ingress      gopkg-charmed:ingress                 ingress         regular
   nginx-ingress-integrator:nginx-peers  nginx-ingress-integrator:nginx-peers  nginx-instance  peer

.. SPREAD SKIP END

The ``ingress`` row is the integration you created; the two ``peer`` rows
are internal to each charm.

Run a health check through ingress:

.. code-block:: bash

   curl --fail --silent --show-error \
     http://${INGRESS_HOST}/health-check \
     --resolve ${INGRESS_HOST}:80:127.0.0.1 | grep -Fx ok

The output is ``ok``. This is where the ``--resolve`` option pins
``INGRESS_HOST`` to ``127.0.0.1``: the request carries the hostname, so the
routing rule matches, but it is sent to the ingress controller on your
machine.

Verify the go-import metadata that the Go tool reads when it resolves an
import path:

.. code-block:: bash

   curl --fail --silent --show-error \
     "http://${INGRESS_HOST}/yaml.v2?go-get=1" \
     --resolve ${INGRESS_HOST}:80:127.0.0.1 | grep go-import

The output contains a ``go-import`` meta tag.

Update the hostname
-------------------

The ``hostname`` configuration option of ``gopkg-charmed`` is the name the
service writes into its ``go-import`` metadata and package links, so it must
be the public name that Go clients use to reach the service. In production
you set it to your domain; here, change it to see that the charm applies a
configuration change to the running service without a rebuild:

.. code-block:: bash

   juju config gopkg-charmed hostname=staging.example.com

.. SPREAD
   juju wait-for application gopkg-charmed \
     --query='status=="active"' --timeout=15m
.. SPREAD END

The charm delivers the new value by restarting the workload in place, so
the old hostname can be served for a few more seconds. Query again until
the new value appears:

.. code-block:: bash

   timeout 120 bash -c '
     until curl --fail --silent --show-error \
         "http://${INGRESS_HOST}/yaml.v2?go-get=1" \
         --resolve "${INGRESS_HOST}:80:127.0.0.1" \
         | grep staging.example.com; do
       sleep 5
     done
   '

The output shows the ``go-import`` meta tag with the new hostname.

Clean up
--------

.. SPREAD
   # spread-teardown
.. SPREAD END

The how-to guides listed in the next section continue from the deployment
you just verified, so follow them first before tearing down. When you are done,
destroy the model to remove both applications and their storage:

.. code-block:: bash

   juju destroy-model gopkg-charmed --destroy-storage --no-prompt

If you no longer need the Juju controller either, remove it as well:

.. code-block:: bash

   juju destroy-controller dev --destroy-all-models --destroy-storage --no-prompt

Both commands wait until the resources are gone and fail if they cannot
remove them.

If you created a Multipass VM for this tutorial, delete it from the host once
you no longer need it:

.. SPREAD SKIP

.. code-block:: bash

   multipass delete --purge charm-dev

.. SPREAD SKIP END

What to read next
-----------------

- :ref:`Configure ingress <configure-ingress>`
- :ref:`Configure hostname <configure-hostname-and-check-go-import>`
- :ref:`Troubleshoot deployment <troubleshoot-deployment>`

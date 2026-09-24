.. _deploy-and-verify-on-kubernetes:

.. meta::
   :description: Deploy the published gopkg-k8s charm on Kubernetes with Juju, publish the service under a hostname, and verify its go-import metadata.

Deploy and verify gopkg-k8s on Kubernetes
=============================================

``gopkg.in`` gives Go programs stable, major-version-specific import paths:
``gopkg.in/yaml.v2`` resolves to the newest v2 tag of the ``go-yaml/yaml``
repository. By the end of this tutorial you will have your own copy of that
service answering the Go tool under a configured hostname, running on
Kubernetes under Juju, with the charm Canonical maintains to run the public
``gopkg.in``. A deployment serves imports of its own hostname, so it is a
mirror or a private import domain, not a replacement for the public service
in code that already imports ``gopkg.in/...``.

The charm is published on `Charmhub <https://charmhub.io/gopkg-k8s>`_
together with the container image it runs, so a deployment is a single
``juju deploy``. This tutorial deploys it on a local MicroK8s cluster,
publishes the service under a hostname through an ingress, and verifies that
the service answers the query the Go tool sends.

What you'll do
--------------

1. Deploy the charm to a new model
2. Publish the service under a hostname
3. Verify the deployment
4. Update the hostname
5. Clean up

Prerequisites
-------------

You need an AMD64 workstation and the environment from
:ref:`set-up-a-local-linux-environment`. After following that guide, you'll
have an Ubuntu environment with the required tools, and your user will belong
to the MicroK8s group. For ARM64 support, see
:ref:`improve-code`.

Confirm that MicroK8s access is ready. This repeats the setup guide's check on
purpose: a shell opened before you joined the group fails here rather than in
the middle of the deployment:

.. code-block:: bash

   id -nG | grep -qw snap_microk8s
   microk8s status --wait-ready

The group check prints nothing, and the status command reports ``microk8s is
running`` with the add-ons listed. If either fails, see
:ref:`troubleshoot-deployment`.

Bootstrap a Juju controller on the MicroK8s cloud. The controller is the
management service that every ``juju`` command talks to:

.. code-block:: bash

   juju bootstrap microk8s dev

Deploy the charm to a new model
-------------------------------

A Juju model is a workspace that holds a set of applications; on Kubernetes,
each model is a namespace. Create one for this deployment:

.. code-block:: bash

   juju add-model gopkg-k8s

Deploy the charm from Charmhub:

.. code-block:: bash

   juju deploy gopkg-k8s --channel latest/edge

Charmhub supplies the charm and its ``app-image`` resource, the container
image that carries the compiled ``gopkg.in`` service, so the command needs no
``--resource`` option. ``latest/edge`` receives a new revision from every
change merged to the charm's main branch and is the only channel published
currently. Juju downloads the charm, pulls the image, and starts the workload; the
application reports ``waiting`` or ``maintenance`` until it is ready.

Publish the service under a hostname
------------------------------------

On its own, the service is reachable only inside the cluster. To publish it
under a hostname, deploy the `NGINX ingress integrator
<https://charmhub.io/nginx-ingress-integrator>`_ from Charmhub. That
charm does not serve traffic itself: it configures the ingress controller
that the MicroK8s ``ingress`` add-on runs, and ``--trust`` grants it the
Kubernetes permissions it needs to create ingress resources:

.. code-block:: bash

   juju deploy nginx-ingress-integrator --channel=latest/stable --trust

Integrate the two applications:

.. code-block:: bash

   juju integrate nginx-ingress-integrator gopkg-k8s

Over the relation, ``gopkg-k8s`` tells
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

Set the workload hostname to the same name:

.. code-block:: bash

   juju config gopkg-k8s hostname=${INGRESS_HOST}

The ``hostname`` option of ``gopkg-k8s`` is the name the service writes into
its ``go-import`` metadata and package links. It is separate from
``service-hostname``, which only decides which requests reach the service,
and neither setting updates the other. The Go tool rejects metadata whose
import prefix differs from the hostname it requested, so the two must carry
the same public name.

.. SPREAD
   juju wait-for application gopkg-k8s \
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

.. vale off

.. terminal::
   :output-only:

   Model          Controller  Cloud/Region        Version  SLA          Timestamp
   gopkg-k8s  dev         microk8s/localhost  3.6.28   unsupported  22:13:30Z

   App                       Version  Status  Scale  Charm                     Channel        Rev  Address         Exposed  Message
   gopkg-k8s                      active      1  gopkg-k8s                 latest/edge      3  10.152.183.31   no
   nginx-ingress-integrator  24.2.0   active      1  nginx-ingress-integrator  latest/stable  203  10.152.183.208  no

   Unit                         Workload  Agent  Address      Ports  Message
   gopkg-k8s/0*             active    idle   10.1.58.140
   nginx-ingress-integrator/0*  active    idle   10.1.58.141

   Integration provider                  Requirer                              Interface       Type     Message
   gopkg-k8s:secret-storage          gopkg-k8s:secret-storage          secret-storage  peer
   nginx-ingress-integrator:ingress      gopkg-k8s:ingress                 ingress         regular
   nginx-ingress-integrator:nginx-peers  nginx-ingress-integrator:nginx-peers  nginx-instance  peer

.. vale on

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

Send the query that the Go tool sends when it resolves an import path, and
check the ``go-import`` meta tag it answers with:

.. code-block:: bash

   curl --fail --silent --show-error \
     "http://${INGRESS_HOST}/yaml.v2?go-get=1" \
     --resolve ${INGRESS_HOST}:80:127.0.0.1 \
     | grep -F "content=\"${INGRESS_HOST}/yaml.v2 git https://${INGRESS_HOST}/yaml.v2\""

The output is the meta tag:

.. terminal::
   :output-only:

   <meta name="go-import" content="gopkg.example.com/yaml.v2 git https://gopkg.example.com/yaml.v2">

The first word of ``content`` is the import prefix. ``go get
gopkg.example.com/yaml.v2`` only accepts the tag because that prefix matches
the import path it asked for, which is why ``grep`` checks the whole content
rather than only that a tag exists.

Update the hostname
-------------------

In production you set both hostname settings to your domain. Here, move
them to a new name to see that the charms apply a configuration change to
the running deployment without a rebuild:

.. code-block:: bash

   export INGRESS_HOST=staging.example.com
   juju config nginx-ingress-integrator service-hostname=${INGRESS_HOST}
   juju config gopkg-k8s hostname=${INGRESS_HOST}

.. SPREAD
   juju wait-for application gopkg-k8s \
     --query='status=="active"' --timeout=15m
   juju wait-for application nginx-ingress-integrator \
     --query='status=="active"' --timeout=15m
.. SPREAD END

The integrator rewrites the routing rule, and the ``gopkg-k8s`` charm
delivers its new value by restarting the workload in place, so for a few
seconds the new name is not routed yet or the old hostname is still served.
Query the new name until the new value appears:

.. code-block:: bash

   timeout 120 bash -c '
     until curl --fail --silent --show-error \
         "http://${INGRESS_HOST}/yaml.v2?go-get=1" \
         --resolve "${INGRESS_HOST}:80:127.0.0.1" \
         | grep -F "content=\"${INGRESS_HOST}/yaml.v2 git https://${INGRESS_HOST}/yaml.v2\""; do
       sleep 5
     done
   '

The output is the ``go-import`` meta tag with ``staging.example.com`` as the
import prefix.

Clean up
--------

.. SPREAD
   # spread-teardown
.. SPREAD END

The how-to guides listed in the next section continue from the deployment
you just verified, so follow them first before tearing down. When you are done,
destroy the model to remove both applications and their storage:

.. code-block:: bash

   juju destroy-model gopkg-k8s --destroy-storage --no-prompt

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
- :ref:`Improve the code <improve-code>`, which builds the rock and the charm
  from source

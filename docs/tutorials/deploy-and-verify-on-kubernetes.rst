.. _deploy-and-verify-on-kubernetes:

.. meta::
   :description: Deploy the published gopkg-k8s charm on Kubernetes with Juju, publish the service under a hostname, verify its go-import metadata, and fetch a module through it with the Go tool.

Deploy and verify gopkg-k8s on Kubernetes
=============================================

``gopkg.in`` gives Go programs stable, major-version-specific import paths:
``gopkg.in/yaml.v2`` resolves to the newest v2 tag of the ``go-yaml/yaml``
repository. By the end of this tutorial you will have your own copy of that
service running on Kubernetes under Juju, with the charm Canonical maintains
to run the public ``gopkg.in``, and a Go program on your machine whose
``gopkg.in/yaml.v2`` import the Go tool fetched through your copy rather
than through the public service.

The charm is published on `Charmhub <https://charmhub.io/gopkg-k8s>`_
together with the container image it runs, so a deployment is a single
``juju deploy``. This tutorial deploys it on a local MicroK8s cluster,
publishes the service under a hostname through an ingress, verifies that
the service answers the query the Go tool sends, then switches it to the
``gopkg.in`` name and lets the Go tool fetch a module through it.

What you'll do
--------------

1. Deploy the charm to a new model
2. Publish the service under a hostname
3. Verify the deployment
4. Switch the hostname to gopkg.in
5. Fetch a module with the Go tool
6. Clean up

Prerequisites
-------------

You need an AMD64 workstation with at least 4 CPU cores, 8 GB of RAM, 50 GB
of disk space, and network access for snaps, Charmhub, and container images.
The published charm and its image are built for AMD64 only; to build them
yourself, or to run them on ARM64, see :ref:`improve-code`.

This tutorial uses `Multipass <https://canonical.com/multipass>`_ to create an
Ubuntu 24.04 LTS virtual machine, so the same steps apply on Linux, macOS, and
Windows hosts, and the VM keeps everything the tutorial installs separate from
your workstation. Install it by following :ref:`Install Multipass
<multipass:how-to-guides-install-multipass>`, then create and enter the VM:

.. SPREAD SKIP

.. code-block:: bash

   multipass launch 24.04 --cpus 4 --disk 50G --memory 8G --name charm-dev
   multipass shell charm-dev

.. SPREAD SKIP END

If your workstation already runs Ubuntu 24.04 LTS, you can skip the virtual
machine and run the remaining steps directly on it. Be aware of what that
means: the steps install snaps with ``sudo``, add your user to the
``snap_microk8s`` group, start a MicroK8s cluster whose ingress listens on
ports 80 and 443 of the workstation, and point the name ``gopkg.in`` at the
workstation itself in ``/etc/hosts`` until the clean-up section removes the
entry.

Install Juju, MicroK8s, and Go from their snaps, and curl and git from the
Ubuntu archive: curl runs the checks later in the tutorial, and the Go tool
clones packages with git. The `Juju
<https://canonical.com/juju/docs/juju-cli/3.6/howto/manage-juju/>`_ and
`MicroK8s <https://canonical.com/microk8s/docs/getting-started>`_
documentation cover other ways to install them; the channels below are the
ones this tutorial was verified with, as listed in
:ref:`platforms-and-prerequisites`:

.. code-block:: bash

   sudo apt update
   sudo apt install --yes curl git
   sudo snap install go --classic
   sudo snap install juju --channel 3/stable
   sudo snap install microk8s --channel 1.36-strict/stable

MicroK8s only accepts commands from members of its group, so add your user to
it, then log out of the VM so the membership applies:

.. SPREAD SKIP

.. code-block:: bash

   sudo adduser $USER snap_microk8s
   exit

``exit`` ends the session and returns you to the host, so run the next
command there to open a new one:

.. code-block:: bash

   multipass shell charm-dev

.. SPREAD SKIP END

.. SPREAD
   sudo adduser $USER snap_microk8s
   # spread-session-break
.. SPREAD END

Confirm the membership in the new session, wait for the cluster, and enable
the add-ons the deployment needs: ``dns`` resolves names inside the cluster,
``hostpath-storage`` provides the volumes the Juju controller requests, and
``ingress`` runs the ingress controller that publishes the service on ports
80 and 443:

.. code-block:: bash

   id -nG | grep -qw snap_microk8s
   microk8s status --wait-ready
   sudo microk8s enable dns hostpath-storage ingress
   microk8s status --wait-ready

The group check prints nothing, and the last command reports ``microk8s is
running`` with the three add-ons under ``enabled``. If the group check fails,
the shell predates the membership: log out and in again. See
:ref:`troubleshoot-deployment` for other failures.

.. note::

   In an interactive shell, ``newgrp snap_microk8s`` applies the membership
   without logging out. It starts a new shell, so any commands you paste
   together with it run in the original shell, before the membership applies.

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

.. SPREAD
   juju status --relations | grep -F 'nginx-ingress-integrator:ingress' \
     | grep -F 'gopkg-k8s:ingress' | grep -Fw regular
.. SPREAD END

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

The first word of ``content`` is the import prefix. The Go tool only accepts
the tag when that prefix matches the import path it asked for, which is why
``grep`` checks the whole content rather than only that a tag exists.

Switch the hostname to gopkg.in
-------------------------------

In production you set both hostname settings to your domain. Here, move
them to ``gopkg.in`` itself, which the next section needs, and see that the
charms apply a configuration change to the running deployment without a
rebuild:

.. code-block:: bash

   export INGRESS_HOST=gopkg.in
   juju config nginx-ingress-integrator service-hostname=${INGRESS_HOST}
   juju config gopkg-k8s hostname=${INGRESS_HOST}

The name is not arbitrary. Every Go module states its own name in its
``go.mod`` file, and the Go tool refuses a module that it fetched under a
different name. ``yaml.v2`` calls itself ``gopkg.in/yaml.v2``, so a
deployment named ``gopkg.example.com`` can hand the package out, but the Go
tool then rejects it with ``module declares its path as: gopkg.in/yaml.v2``.
A deployment under a name of your own can serve packages that use that name
in their ``go.mod``, or old packages that have no ``go.mod`` at all. To
serve the packages the public ``gopkg.in`` is known for, it must be called
``gopkg.in``.

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

The output is the ``go-import`` meta tag with ``gopkg.in`` as the import
prefix.

Fetch a module with the Go tool
-------------------------------

Until now, ``--resolve`` told curl to send its requests for the hostname to
your own machine, ``127.0.0.1``, instead of looking the name up. The Go tool
and git have no such option: given ``gopkg.in``, they look the name up and
reach the public service. To send them to your deployment instead, add a
line to ``/etc/hosts``, the file every program on the machine checks before
asking DNS. With ``gopkg.in`` mapped to ``127.0.0.1`` there, anything that
connects to ``gopkg.in`` reaches the ingress controller on your machine
while still asking for the name ``gopkg.in``, which is what the routing
rule matches. Add the line, then repeat the health check without
``--resolve`` to see it work:

.. code-block:: bash

   echo "127.0.0.1 gopkg.in" | sudo tee -a /etc/hosts
   curl --fail --silent --show-error http://gopkg.in/health-check | grep -Fx ok

Create a Go module with a program that imports ``gopkg.in/yaml.v2``:

.. code-block:: bash

   mkdir -p ~/gopkg-try
   cd ~/gopkg-try
   go mod init example.com/try
   cat > main.go <<'EOF'
   package main

   import (
       "fmt"

       "gopkg.in/yaml.v2"
   )

   func main() {
       var doc map[string]string
       if err := yaml.Unmarshal([]byte("source: gopkg.in/yaml.v2"), &doc); err != nil {
           panic(err)
       }
       fmt.Println(doc["source"])
   }
   EOF

Fetch the module. Three environment variables keep the Go tool on your
deployment. The last two switch off certificate checks, so set them only
for a deployment you run yourself, as here:

``GOPRIVATE=gopkg.in``
  Fetch ``gopkg.in`` paths from their source rather than through the public
  module proxy and checksum database. Without it, the proxy answers and
  your deployment is never asked.

``GOINSECURE=gopkg.in``
  Accept the certificate the ingress controller presents on port 443. It is
  a self-signed placeholder, because nothing in this tutorial issued a
  certificate for ``gopkg.in``.

``GIT_SSL_NO_VERIFY=true``
  The same for git, which the Go tool runs to clone from the
  ``https://gopkg.in/yaml.v2`` address that the ``go-import`` metadata
  names.

.. code-block:: bash

   export GOPRIVATE=gopkg.in GOINSECURE=gopkg.in GIT_SSL_NO_VERIFY=true
   go get gopkg.in/yaml.v2

The Go tool queries ``https://gopkg.in/yaml.v2?go-get=1``, reads the
``go-import`` tag you checked earlier, clones the repository it names, and
records the newest v2 tag in ``go.mod``:

.. terminal::
   :output-only:

   go: downloading gopkg.in/yaml.v2 v2.4.0
   go: added gopkg.in/yaml.v2 v2.4.0

.. SPREAD
   grep -F 'gopkg.in/yaml.v2 v2' go.mod
.. SPREAD END

Build and run the program:

.. code-block:: bash

   go run .

.. SPREAD
   go run . | grep -Fx gopkg.in/yaml.v2
.. SPREAD END

It prints ``gopkg.in/yaml.v2``. Nothing so far shows where the package came
from, so read the service's request counters through the ingress.
``git_upload_pack`` is the route that serves a clone, and only git calls it:

.. code-block:: bash

   curl --fail --silent --show-error http://gopkg.in/metrics \
     | grep '^gopkg_http_requests_total{.*route="git_upload_pack"'

The output is that counter with a value of at least 1. The exact value
depends on how many fetches the Go tool split the work into, and it also
fetched ``gopkg.in/check.v1``, a test dependency of ``yaml.v2``, the same
way:

.. terminal::
   :output-only:

   gopkg_http_requests_total{method="POST",route="git_upload_pack",status_code="200"} 3

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

Remove the ``/etc/hosts`` entry so that ``gopkg.in`` resolves to the public
service again. The variables you exported last only for the shell session:

.. code-block:: bash

   sudo sed -i '/^127.0.0.1 gopkg.in$/d' /etc/hosts

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

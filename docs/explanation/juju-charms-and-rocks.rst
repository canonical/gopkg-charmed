.. _juju-charms-and-rocks:

.. meta::
  :description: Understand how the gopkg rock, the gopkg-charmed charm, and Juju fit together to run gopkg.in on Kubernetes.

Juju, charms, and rocks
=======================

Running ``gopkg.in`` on Kubernetes involves three pieces: a **rock**, a
**charm**, and **Juju**. The rock contains the application, the charm contains
the instructions for operating it, and Juju follows those instructions on a
Kubernetes cluster. This page describes what each piece is for this project
and where it lives in the repository; the linked upstream documentation
covers the tools themselves.

Application
-----------

The application is the Go program that serves ``gopkg.in`` requests, with its
source in ``app/*.go``. It is a plain HTTP server configured through
environment variables such as ``APP_PORT`` and ``APP_HOSTNAME``. Kubernetes
runs it from a container image, and that image is the rock.

Rock
----

A **rock** is a container image built with Rockcraft from Ubuntu packages.
The rock for this project is built with ``base: bare``, so it carries no
Ubuntu base system: only the compiled ``gopkg.in`` application and the
slices of Ubuntu packages it needs to run, which are CA certificates,
``bash``, and ``coreutils``. Its build recipe is ``app/rockcraft.yaml``. The
recipe uses the Go framework extension, which supplies the standard build
and runtime setup for a Go web application.

The rock does not decide when to deploy ``gopkg.in``, how to react to
configuration changes, or how to connect the application to other services.
It only provides the runnable workload. Those operational decisions belong to
the charm.

Learn more from the official documentation:

- :ref:`What rocks are <rockcraft:explanation-rocks>`
- :ref:`Go framework extension <rockcraft:reference-go-framework>`
- :doc:`Build a rock for a Go application <rockcraft:tutorial/go>`

Charm
-----

A **charm** is a software package containing the knowledge needed to operate
an application. The ``gopkg-charmed`` charm tells Juju how to run the gopkg
rock on Kubernetes: it configures and starts the workload, passes the
configured hostname to the process as ``APP_HOSTNAME``, integrates with an
ingress charm for external HTTP routing and TLS termination, and reports the
workload's health through a health endpoint and Juju status. Its definition
is ``app/charm/charmcraft.yaml``, and its entry point is
``app/charm/src/charm.py``.

``gopkg-charmed`` is a 12-factor app charm. Charmcraft's Go framework
extension and the ``paas_charm`` library implement the workload lifecycle, so
the project-specific charm code stays small.

Learn more from the official documentation:

- :ref:`What a charm is <juju:charm>`
- :ref:`Go framework extension <charmcraft:go-framework-extension>`
- :doc:`Manage a 12-factor app charm <charmcraft:howto/manage-web-app-charms/index>`
- :ref:`Write your first Kubernetes charm for a Go app <charmcraft:write-your-first-kubernetes-charm-for-a-go-app>`

Juju
----

**Juju** deploys and operates applications from charms. For this project the
target cloud is a Kubernetes cluster, and the tutorial's deployment uses these
Juju objects:

- The :ref:`controller <juju:controller>` ``dev``, created by
  ``juju bootstrap``, coordinates all work on the cluster.
- The :ref:`model <juju:model>` ``gopkg-charmed`` groups the deployment.
- ``gopkg-charmed`` and ``nginx-ingress-integrator`` are two
  :ref:`applications <juju:application>` in that model, each running as one
  :ref:`unit <juju:unit>`.
- An :ref:`integration <juju:relation>` between the two applications carries
  the routing data the ingress needs.

Juju asks Kubernetes for the pods and containers; the charm configures and
starts ``gopkg.in`` inside them.

Putting it together
-------------------

1. Rockcraft builds the gopkg rock from ``app/rockcraft.yaml``, and the rock
   is pushed to a container registry.
2. Charmcraft builds the ``gopkg-charmed`` charm from ``app/charm/``.
3. Juju deploys the charm with the rock as its ``app-image`` resource, and
   the charm starts ``gopkg.in`` in the workload container.
4. Configuration changes and integrations reach the charm as Juju events, and
   the charm updates the running workload.

Follow :ref:`deploy-and-verify-on-kubernetes` to build each artifact and see
the complete deployment flow, then read :doc:`Ingress <ingress>` to
understand how requests reach ``gopkg-charmed`` from outside the cluster.

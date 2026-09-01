.. _juju-charms-and-rocks:

Juju, charms, and rocks
=======================

Running ``gopkg.in`` on Kubernetes involves three important pieces: a
**rock**, a **charm**, and **Juju**. Each has a different job.

The shortest explanation is:

- The **rock** contains the application.
- The **charm** contains instructions for operating the application.
- **Juju** follows those instructions on a cloud, which is Kubernetes for
  ``gopkg-charmed``.

It may help to think of the rock as the packaged application, the charm as its
operations manual, and Juju as the operator that follows the manual. The
sections below explain where that comparison is useful and what each piece
really does.

The application comes first
---------------------------

The application is the Go program that serves ``gopkg.in`` requests. On its
own, it can run as a normal process. It listens for HTTP requests and uses
environment variables such as ``APP_PORT`` and ``APP_HOSTNAME``.

Kubernetes does not run source code directly. It runs containers created from
container images. The Go application must therefore be built and placed in a
container image before Kubernetes can run it. That image is the rock.

What is a rock?
---------------

A **rock** is an Ubuntu-based container image. It follows the Open Container
Initiative image standard, so Kubernetes and other standard container tools
can run it.

The rock for this project contains the compiled ``gopkg.in`` application and
the files needed to start it. Its build recipe is ``app/rockcraft.yaml``. The
recipe uses the Go framework extension, which supplies the standard build and
runtime setup for a Go web application.

`Rockcraft <https://ubuntu.com/containers/rockcraft/docs/latest/>`_ is the
command-line tool that builds rocks. Running ``rockcraft pack`` reads
``rockcraft.yaml`` and produces a ``.rock`` file. The resulting image can then
be uploaded to a container registry, where Kubernetes can retrieve it.

A rock does not decide when to deploy, how to react to configuration changes,
or how to connect the application to other services. It only provides the
runnable workload. Those operational decisions belong to the charm.

Learn more from the official documentation:

- `What rocks are <https://ubuntu.com/containers/rockcraft/docs/latest/explanation/rocks/>`_
- `Create your first rock <https://ubuntu.com/containers/rockcraft/docs/latest/tutorial/hello-world/>`_
- `Build a rock for a Go application <https://ubuntu.com/containers/rockcraft/docs/latest/tutorial/go/>`_

What is a charm?
----------------

A **charm** is a software package containing the knowledge needed to operate
an application. It describes the application to Juju and includes code that
responds to events such as deployment, configuration changes, integration
with another application, and removal.

The ``gopkg-charmed`` charm tells Juju how to run the gopkg rock. For example,
it passes the configured ``hostname`` value to the Go process as
``APP_HOSTNAME``. It also exposes the information needed to integrate the
application with an ingress charm, which makes the HTTP service reachable
from outside the Kubernetes cluster.

The charm package and the rock are separate artifacts:

- The **rock** answers the question, "What process runs in the container?"
- The **charm** answers the question, "How should that process be operated?"

`Charmcraft <https://canonical.com/juju/docs/charmcraft/4/>`_ is the
command-line tool used to build charms. Running ``charmcraft pack`` reads
``app/charm/charmcraft.yaml`` and packages the charm code and metadata into a
``.charm`` file.

This project uses a `Canonical 12-factor app charm
<https://canonical.com/juju/docs/charmcraft/stable/howto/manage-web-app-charms/>`_.
The
`Twelve-Factor App <https://12factor.net/>`_ methodology describes practices
for building portable services, including keeping configuration in the
environment and separating build and run stages. Charmcraft's Go framework
extension and the ``paas_charm`` library apply those patterns to common
operations for a Go web service. As a result, the project-specific charm code
can stay small while still handling the workload lifecycle through Juju.

Learn more from the official documentation:

- `What a charm is <https://canonical.com/juju/docs/juju-cli/3.6/reference/charm/>`_
- `Charmcraft documentation <https://canonical.com/juju/docs/charmcraft/4/>`_
- `Write your first Kubernetes charm for a Go application <https://canonical.com/juju/docs/charmcraft/4/tutorial/kubernetes-charm-go/>`_

What is Juju?
-------------

`Juju <https://canonical.com/juju/docs/juju-cli/3.6/>`_ is an application
orchestration tool. You describe the result you want with commands such as
``juju deploy``, ``juju config``, and ``juju integrate``. Juju then uses charms
to create and operate the applications on the target cloud.

For this project, the target cloud is a Kubernetes cluster. Juju works with
Kubernetes rather than replacing it:

- Kubernetes schedules containers and provides cluster resources.
- Juju manages applications and their relationships.
- The charm translates Juju operations into application-specific changes.

Several Juju terms appear throughout this documentation:

**Controller**
  The Juju control plane. It receives commands, stores the desired state, and
  coordinates work on the target cloud. ``juju bootstrap`` creates one.

**Model**
  A workspace inside a controller. It groups applications that belong
  together. ``juju add-model gopkg-charmed`` creates the model used by the
  local deployment guides.

**Application**
  A deployed charm managed by Juju. ``gopkg-charmed`` and
  ``nginx-ingress-integrator`` are two separate applications in the same
  model.

**Unit**
  One running instance of an application. For this Kubernetes charm, a unit
  corresponds to a Kubernetes pod containing the charm and workload
  containers.

**Integration**
  A declared connection between two applications. The command
  ``juju integrate nginx-ingress-integrator gopkg-charmed`` lets the charms
  exchange the information required to route requests to the Go service.

Learn more from the official documentation:

- `Get started with Juju <https://canonical.com/juju/docs/juju-cli/3.6/tutorial/>`_
- `Juju documentation <https://canonical.com/juju/docs/juju-cli/3.6/>`_
- `How Juju models applications <https://canonical.com/juju/docs/juju-cli/3.6/explanation/application-modelling/>`_

How the pieces work together
----------------------------

The complete path from source code to a running service is:

1. The Go compiler builds the ``gopkg.in`` application.
2. Rockcraft packages the application as the gopkg rock.
3. The rock is pushed to a container registry.
4. Charmcraft packages the ``gopkg-charmed`` operations code as a charm.
5. An operator asks Juju to deploy the charm and supplies the rock as its
   application image.
6. Juju asks Kubernetes to create the required pod and containers.
7. The charm configures and starts the application from the rock.
8. When an operator changes configuration or adds an integration, Juju sends
   that event to the charm. The charm updates the workload accordingly.

In commands, the central part of that flow looks like this:

.. code-block:: text

   rockcraft pack        -> build the application image
   charmcraft pack       -> build the operations package
   juju deploy           -> create and operate the application
   juju config           -> change application configuration
   juju integrate        -> connect applications
   juju status           -> show their current state

The tools produce or manage different things. Rockcraft does not deploy the
application, Charmcraft does not run it, and Juju does not compile it. Keeping
these responsibilities separate makes the same application image repeatable,
the same operational behavior reusable, and the deployment manageable through
one interface.

How this maps to the repository
-------------------------------

The relevant files are organized by responsibility:

- ``app/*.go`` contains the application source code.
- ``app/rockcraft.yaml`` describes how to build the rock.
- ``app/charm/charmcraft.yaml`` describes the charm and its configuration.
- ``app/charm/src/charm.py`` is the charm entry point.

With these concepts in place, follow :ref:`deploy-and-verify-on-kubernetes` to
build each artifact and see the complete deployment flow.

Next, read :doc:`Ingress <ingress>` to understand how requests reach
``gopkg-charmed`` from outside the Kubernetes cluster.
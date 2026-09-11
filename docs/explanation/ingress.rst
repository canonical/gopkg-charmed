.. _ingress:

.. meta::
  :description: Understand how ingress routes external requests to gopkg-charmed on Kubernetes and how DNS, Services, and TLS fit together.

Ingress
=======

``gopkg-charmed`` runs inside Kubernetes. By default, its service is reachable
only by other workloads in the cluster. Ingress provides a controlled route
from an external hostname, such as ``gopkg.example.com``, to that internal
service.

For a complete deployment, follow :ref:`deploy-and-verify-on-kubernetes`. To
change the routing rules, add DNS, or enable HTTPS, follow
:ref:`configure-ingress`.

What Ingress solves
-------------------

Kubernetes gives the application a private Service and a cluster-local address.
That address can change and is normally unavailable to clients outside the
cluster. Ingress adds a stable entry point and routing rules in front of the
Service.

An incoming request follows this path:

.. mermaid::

  flowchart TD
    dns[DNS] -. Resolves host .-> client[Client]
    client -->|GET /yaml.v2| ingress[Ingress controller]
    ingress --> service[Kubernetes Service]
    service --> app[gopkg.in]

The same ingress endpoint can serve several applications. The controller uses
the request's hostname and path to select the correct backend.

The components and their responsibilities
-----------------------------------------

Several components cooperate to provide ingress. They are related, but they
are not interchangeable.

**The gopkg-charmed application**
  Runs the ``gopkg.in`` workload. The Go framework extension creates the
  Kubernetes Service and provides the relation data needed to expose it.

**The Kubernetes Service**
  Gives the application units one stable internal destination. Ingress sends
  matching traffic to this Service instead of addressing a pod directly.

**The Kubernetes Ingress resource**
  Describes routing rules, including the external hostname, paths, backend
  Service, and optional TLS certificate. It is configuration stored in the
  Kubernetes API; it does not process traffic itself.

**The ingress controller**
  Watches Ingress resources and implements their rules. It is the component
  that listens for HTTP or HTTPS traffic and proxies matching requests to
  Services. A cluster must have a compatible controller before an Ingress
  resource can work.

**The nginx-ingress-integrator charm**
  Converts Juju configuration and relation data into a Kubernetes Ingress
  resource. It does not replace the ingress controller. The ``--trust`` option
  allows the charm to manage the required cluster resources.

**DNS**
  Directs the public hostname to the ingress controller's external address.
  Configuring ``service-hostname`` creates a routing rule, but it does not
  create a DNS record.

How Juju connects the applications
----------------------------------

Running ``juju integrate nginx-ingress-integrator gopkg-charmed`` creates a
Juju integration. Through it, ``gopkg-charmed`` supplies its Service name,
namespace, and port. The integrator combines that information with its own
configuration and creates the Ingress resource. Juju keeps the relationship
up to date when either application changes.

The integration must be in the same Juju model as both applications. For a
Kubernetes cloud, the model corresponds to a Kubernetes namespace.

Why the guides pin the hostname locally
---------------------------------------

The documentation hostname ``gopkg.example.com`` does not resolve to the local
machine automatically. The guides therefore use curl's ``--resolve`` option to
supply the address for one request without changing DNS or ``/etc/hosts``.
``--resolve`` makes curl connect to ``127.0.0.1`` while still sending
``Host: gopkg.example.com``. The Host header matters because the ingress rule
uses it to choose the backend, so a request without the hostname never
matches the rule.

This works because the MicroK8s ingress controller listens on the local
loopback interface. From another machine, the same request must target the
address of the machine or load balancer that exposes the controller.

The two hostname settings
-------------------------

This deployment has two independent hostname settings:

``nginx-ingress-integrator service-hostname``
  Controls which incoming HTTP hostname routes to the application.

``gopkg-charmed hostname``
  Becomes ``APP_HOSTNAME`` inside the workload. It controls the hostname shown
  in package links and ``go-import`` metadata.

For a normal deployment, both are set to the public hostname. They can differ
for testing: clients then enter through the ingress hostname, but responses
advertise the workload hostname. Changing one setting does not update the
other, which is why :ref:`configure-ingress` sets both.

Where TLS terminates
--------------------

TLS is normally terminated at the ingress controller. The client establishes
HTTPS with the controller, and the controller forwards the request to the
internal Service over the cluster network. The certificate therefore has to
cover the public hostname, and it lives in the model's Kubernetes namespace,
where the integrator can reference it by secret name.

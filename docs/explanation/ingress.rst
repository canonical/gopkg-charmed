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

How a request reaches the workload
----------------------------------

.. mermaid::

  flowchart TD
    dns[DNS] -. Resolves host .-> client[Client]
    client -->|GET /yaml.v2| ingress[Ingress controller]
    ingress --> service[Kubernetes Service]
    service --> app[gopkg.in]

Kubernetes `Ingress resources
<https://kubernetes.io/docs/concepts/services-networking/ingress/>`__ hold
the routing rules, and an `ingress controller
<https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/>`__
implements them by forwarding matching requests to a Service; the Kubernetes
documentation describes both. In this deployment:

- ``gopkg-charmed`` runs the ``gopkg.in`` workload. The Go framework
  extension creates the Kubernetes Service and provides the relation data
  needed to expose it.
- The `nginx-ingress-integrator
  <https://charmhub.io/nginx-ingress-integrator>`__ charm turns its Juju
  configuration and that relation data into the Ingress
  resource. It does not replace the ingress controller, which MicroK8s
  provides through its ``ingress`` add-on, and it needs ``--trust`` to manage
  cluster resources.
- DNS stays outside the cluster. Setting ``service-hostname`` creates a
  routing rule, not a DNS record.

How Juju connects the applications
----------------------------------

Running ``juju integrate nginx-ingress-integrator gopkg-charmed`` creates a
Juju integration through which ``gopkg-charmed`` supplies its Service name,
namespace, and port. The integrator combines that information with its own
configuration to create the Ingress resource, and Juju keeps it up to date
when either application changes. The tutorial deploys both applications in
the same model.

Why the guides pin the hostname locally
---------------------------------------

The documentation hostname ``gopkg.example.com`` does not resolve to the local
machine automatically. The guides therefore use curl's ``--resolve`` option to
supply the address for one request without changing DNS or ``/etc/hosts``.
``--resolve`` makes curl connect to ``127.0.0.1`` while still sending
``Host: gopkg.example.com``. The Host header matters because the ingress rule
uses it to choose the backend, so a request without the hostname never
matches the rule.

Connecting to ``127.0.0.1`` reaches the controller because the MicroK8s
ingress controller binds ports 80 and 443 on the node itself, loopback
included. From another machine, the same request must target the address of
the machine or load balancer that exposes the controller.

The two hostname settings
-------------------------

This deployment has two independent hostname settings:

``service-hostname``
  Set in ``nginx-ingress-integrator``. Controls which incoming HTTP hostname routes to the application.

``hostname``
  Set in ``gopkg-charmed``. Becomes ``APP_HOSTNAME`` inside the workload. It controls the hostname shown
  in package links and ``go-import`` metadata.

For a normal deployment, both are set to the public hostname. They can differ
for testing: clients then enter through the ingress hostname, but responses
advertise the workload hostname. Changing one setting does not update the
other, which is why :ref:`configure-ingress` sets both.

Where TLS terminates
--------------------

TLS terminates at the ingress controller, so the certificate must cover the
public hostname. It is stored as a Kubernetes TLS secret in the model's
namespace, where the integrator references it by name through its
``tls-secret-name`` option; :ref:`configure-ingress` shows the steps.

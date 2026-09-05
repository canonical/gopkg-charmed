.. _ingress:

.. meta::
  :description: Understand how ingress routes external requests to gopkg-charmed on Kubernetes and how DNS, Services, and TLS fit together.

Ingress
=======

``gopkg-charmed`` runs inside Kubernetes. By default, its service is reachable
only by other workloads in the cluster. Ingress provides a controlled route
from an external hostname, such as ``gopkg.example.com``, to that internal
service.

For a complete deployment, follow :ref:`deploy-and-verify-on-kubernetes`.

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

The command below creates a Juju integration:

.. code-block:: bash

   juju integrate nginx-ingress-integrator gopkg-charmed

Through this integration, ``gopkg-charmed`` supplies its Service name,
namespace, and port. The integrator combines that information with its own
configuration and creates the Ingress resource. Juju keeps the relationship
up to date when either application changes.

The integration must be in the same Juju model as both applications. For a
Kubernetes cloud, the model corresponds to a Kubernetes namespace.

Set up Ingress on local MicroK8s
--------------------------------

First enable the MicroK8s ingress add-on and wait for the cluster:

.. code-block:: bash

   sudo microk8s enable ingress
   microk8s status --wait-ready

This installs an ingress controller. It is separate from the Juju integrator
charm deployed in the next step.

After deploying ``gopkg-charmed``, deploy and integrate the ingress charm:

.. code-block:: bash

   juju deploy nginx-ingress-integrator --channel=latest/stable --trust
   juju integrate nginx-ingress-integrator gopkg-charmed

Configure one hostname and route every path without rewriting it:

.. code-block:: bash

   export INGRESS_HOST=gopkg.example.com
   juju config nginx-ingress-integrator \
     service-hostname=${INGRESS_HOST} \
     path-routes=/ \
     rewrite-enabled=false

These settings have distinct jobs:

``service-hostname``
  Matches the HTTP ``Host`` header. Only requests for this hostname use the
  rule.

``path-routes``
  Selects the URL paths sent to the application. ``/`` exposes all paths,
  including ``/health-check`` and package paths such as ``/yaml.v2``.

``rewrite-enabled``
  Controls whether the controller changes the path before forwarding it.
  This must be ``false`` because the workload needs the original package path.

Wait for both applications to settle before testing:

.. code-block:: bash

   juju wait-for application gopkg-charmed \
     --query='status=="active"' --timeout=15m
   juju wait-for application nginx-ingress-integrator \
     --query='status=="active"' --timeout=15m

Local hostname resolution
-------------------------

The documentation hostname ``gopkg.example.com`` does not resolve to the local
machine automatically. The tutorials use curl's ``--resolve`` option to supply
the address for one request without changing DNS or ``/etc/hosts``:

.. code-block:: bash

   curl --fail --silent --show-error \
     http://${INGRESS_HOST}/health-check \
     --resolve ${INGRESS_HOST}:80:127.0.0.1

``--resolve`` makes curl connect to ``127.0.0.1`` while still sending
``Host: gopkg.example.com``. The Host header matters because the ingress rule
uses it to choose the backend. This approach is suitable when the MicroK8s
ingress controller is reachable on the local loopback interface.

For access from another machine, use the address of the machine or load
balancer that exposes the controller instead of ``127.0.0.1``. Ensure that
network firewalls allow the required port.

The two hostname settings
-------------------------

This deployment has two independent hostname settings:

``nginx-ingress-integrator service-hostname``
  Controls which incoming HTTP hostname routes to the application.

``gopkg-charmed hostname``
  Becomes ``APP_HOSTNAME`` inside the workload. It controls the hostname shown
  in package links and ``go-import`` metadata.

For a normal deployment, set both to the public hostname:

.. code-block:: bash

   juju config nginx-ingress-integrator \
     service-hostname=gopkg.example.com
   juju config gopkg-charmed hostname=gopkg.example.com

They can differ for testing. In that case, clients enter through the ingress
hostname, but responses advertise the workload hostname. Changing one setting
does not update the other.

Set up production DNS
---------------------

For production, replace the documentation hostname with a domain you control.
The general sequence is:

1. Find the external IP address or hostname of the ingress controller.
2. Create an ``A`` or ``AAAA`` record, or an appropriate ``CNAME`` record, with
   your DNS provider.
3. Set ``service-hostname`` and the ``gopkg-charmed`` ``hostname`` option to
   that domain.
4. Wait for DNS changes to propagate.
5. Verify that ports 80 and 443 reach the ingress controller.

The way an external address is assigned depends on the Kubernetes platform.
A managed cloud commonly provisions a load balancer. A local or bare-metal
cluster may require a node address, port forwarding, or a load-balancer
implementation such as MetalLB.

Enable HTTPS
------------

TLS is normally terminated at the ingress controller. The client establishes
HTTPS with the controller, and the controller forwards the request to the
internal Service.

The certificate must include the public hostname in its subject alternative
names. Store the certificate and private key in a Kubernetes TLS secret in the
same namespace as the Juju model, then configure the integrator with the secret
name. For example, for the ``gopkg-charmed`` model namespace:

.. code-block:: bash

   microk8s kubectl -n gopkg-charmed create secret tls gopkg-tls \
     --cert=path/to/fullchain.pem \
     --key=path/to/private-key.pem
   juju config nginx-ingress-integrator tls-secret-name=gopkg-tls

Use your certificate manager's recommended renewal process. Replacing the
secret data allows the controller to load the renewed certificate. Keep
private keys out of the repository and restrict access to the namespace.

The integrator can also obtain TLS information through a certificate relation.
See the `NGINX ingress integrator documentation
<https://documentation.ubuntu.com/nginx-ingress-integrator-charm/>`_ when using
a certificate provider charm.

Verify routing
--------------

Check Juju status and confirm the integration exists:

.. code-block:: bash

   juju status --relations

Inspect the generated Kubernetes resource when diagnosing routing:

.. code-block:: bash

   microk8s kubectl -n gopkg-charmed get ingress
   microk8s kubectl -n gopkg-charmed describe ingress

Then test both workload behavior and metadata through ingress:

.. code-block:: bash

   curl --fail --silent --show-error \
     http://${INGRESS_HOST}/health-check \
     --resolve ${INGRESS_HOST}:80:127.0.0.1
   curl --fail --silent --show-error \
     "http://${INGRESS_HOST}/yaml.v2?go-get=1" \
     --resolve ${INGRESS_HOST}:80:127.0.0.1 | grep go-import

An ``ok`` health response proves that the controller, routing rule, Service,
and workload all participated in the request. The metadata request also checks
that the application handles a real package path.

Common failure modes
--------------------

**The integrator is blocked**
  Set ``service-hostname`` and check that the Juju integration exists.

**The request returns 404 from the controller**
  Confirm that the request hostname exactly matches ``service-hostname`` and
  that ``path-routes`` includes the requested path. With curl, include the
  correct ``--resolve`` entry.

**The request reaches the wrong application**
  Inspect all Ingress resources for duplicate hostname and path rules. If the
  cluster has several controllers, set the integrator's ``ingress-class`` to
  the class that should implement this route.

**The request redirects or the backend sees the wrong path**
  Confirm that ``rewrite-enabled`` is ``false``.

**The request returns 502 or 503**
  The rule may exist before the backend is ready. Check ``juju status``, the
  application pods, Service endpoints, and ingress-controller logs. Retry only
  after confirming that the applications are active.

**The hostname does not resolve**
  Create or correct the DNS record. For local testing, use ``--resolve`` with
  the controller's reachable address.

**HTTPS reports a certificate error**
  Confirm that the certificate covers the requested hostname, the TLS secret
  is in the model namespace, and ``tls-secret-name`` matches the secret name.

For command-focused recovery steps, see :ref:`troubleshoot-deployment`. For all
supported integrator settings, see the `NGINX ingress integrator configuration
reference <https://charmhub.io/nginx-ingress-integrator/configurations>`_.
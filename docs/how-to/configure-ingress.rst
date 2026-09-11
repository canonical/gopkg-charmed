.. _configure-ingress:

.. meta::
   :description: Route external HTTP traffic to gopkg-charmed with the NGINX ingress integrator, match the workload hostname, add DNS, and enable HTTPS.

Configure ingress
=================

Ingress is what makes ``gopkg-charmed`` reachable from outside the Kubernetes
cluster under a hostname you choose. Set the routing rules on the ingress
integrator, keep the workload hostname in step with them, then point DNS at
the ingress controller and terminate TLS there for production.

These steps assume that ``gopkg-charmed`` and ``nginx-ingress-integrator``
are deployed and integrated, as they are after the deployment steps of
:ref:`deploy-and-verify-on-kubernetes` and before its clean-up section. For
how the components fit together, read :ref:`Ingress <ingress>`.

Set the routing hostname and paths
----------------------------------

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

Match the workload hostname
---------------------------

The ingress hostname and the hostname the application renders in package
links and ``go-import`` metadata are separate settings. For a normal
deployment, set both to the public hostname:

.. code-block:: bash

   juju config gopkg-charmed hostname=${INGRESS_HOST}

Wait for both applications to settle:

.. SPREAD SKIP

.. code-block:: bash

   juju status --watch 2s

.. SPREAD SKIP END

.. SPREAD
   juju wait-for application gopkg-charmed \
     --query='status=="active"' --timeout=15m
   juju wait-for application nginx-ingress-integrator \
     --query='status=="active"' --timeout=15m
.. SPREAD END

Verify routing
--------------

Confirm that the integration exists and inspect the generated Kubernetes
resource:

.. code-block:: bash

   juju status --relations
   microk8s kubectl -n gopkg-charmed get ingress
   microk8s kubectl -n gopkg-charmed describe ingress

Then test both workload behavior and metadata through ingress. The
documentation hostname does not resolve to your machine, so ``--resolve``
pins it to the local ingress controller for each request:

.. code-block:: bash

   curl --fail --silent --show-error --retry 30 --retry-delay 2 \
     --retry-all-errors \
     http://${INGRESS_HOST}/health-check \
     --resolve ${INGRESS_HOST}:80:127.0.0.1 | grep -Fx ok
   curl --fail --silent --show-error --retry 30 --retry-delay 2 \
     --retry-all-errors \
     "http://${INGRESS_HOST}/yaml.v2?go-get=1" \
     --resolve ${INGRESS_HOST}:80:127.0.0.1 | grep go-import

An ``ok`` health response proves that the controller, routing rule, Service,
and workload all participated in the request. The metadata request checks
that the application handles a real package path.

For access from another machine, use the address of the machine or load
balancer that exposes the controller instead of ``127.0.0.1``, and make sure
that network firewalls allow the port.

Set up production DNS
---------------------

For production, replace the documentation hostname with a domain you control:

1. Find the external IP address or hostname of the ingress controller.
2. Create an ``A`` or ``AAAA`` record, or an appropriate ``CNAME`` record, with
   your DNS provider.
3. Set ``service-hostname`` and the ``gopkg-charmed`` ``hostname`` option to
   that domain, as in the sections above.
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

.. SPREAD SKIP

.. code-block:: bash

   microk8s kubectl -n gopkg-charmed create secret tls gopkg-tls \
     --cert=path/to/fullchain.pem \
     --key=path/to/private-key.pem
   juju config nginx-ingress-integrator tls-secret-name=gopkg-tls

.. SPREAD SKIP END

Use your certificate manager's recommended renewal process. Replacing the
secret data allows the controller to load the renewed certificate. Keep
private keys out of the repository and restrict access to the namespace.

The integrator can also obtain TLS information through a certificate relation.
See the `NGINX ingress integrator documentation
<https://canonical.com/juju/docs/nginx-ingress-integrator-charm/latest/>`_ when
using a certificate provider charm.

For all supported integrator settings, see the `NGINX ingress integrator
configuration reference
<https://charmhub.io/nginx-ingress-integrator/configurations>`_. For failure
symptoms and fixes, see :ref:`troubleshoot-deployment`.

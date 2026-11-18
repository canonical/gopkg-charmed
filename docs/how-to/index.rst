.. _how-to-guides:

.. meta::
   :description: Configure, observe, upgrade, and troubleshoot gopkg-k8s with task-focused procedures.

How-to guides
=============

Task-based procedures for exposing the ``gopkg-k8s`` charm to Go clients and
operating it in a Juju-managed Kubernetes environment.

Ingress and networking
----------------------

Make the service reachable from outside the cluster and set the hostname it
advertises to Go clients.

.. toctree::
   :maxdepth: 1

   Configure ingress <configure-ingress>
   Configure hostname <configure-hostname-and-check-go-import>

Operations and maintenance
--------------------------

Monitor the service with COS, upgrade it to a newer charm revision, and
diagnose deployment failures.

.. toctree::
   :maxdepth: 1

   Integrate with COS <integrate-with-cos>
   Upgrade <upgrade-the-charm>
   Troubleshoot deployment issues <troubleshoot-deployment>

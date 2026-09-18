.. _gopkg-service:

.. meta::
   :description: Understand what the gopkg.in service operated by gopkg-k8s does for Go programs, why its import paths still matter, and what the charm adds.

How gopkg.in serves stable import paths
=======================================

``gopkg.in`` is the Go service that ``gopkg-k8s`` operates. This page
describes what the service does for a Go program that imports a ``gopkg.in``
path, why those paths still matter, and what the charm adds. The URL patterns
and version rules of the service itself are documented upstream on the
`gopkg.in page <https://labix.org/gopkg.in>`_, which a deployment's front
page redirects to.

Why gopkg.in exists
-------------------

``gopkg.in`` provides stable, major-version-specific import paths. An import
such as ``gopkg.in/yaml.v2`` names major version 2 of the ``yaml``
repository, and the service resolves it to the newest compatible tag in that
series. The service predates Go modules, which now encode major versions in
module paths themselves; see `Module version numbering
<https://go.dev/doc/modules/version-numbers>`_ and `Major version suffixes
<https://go.dev/ref/mod#major-version-suffixes>`_ in the Go documentation.

Go modules do not remove import paths already published in source code and
``go.mod`` files. Those paths are part of a package's identity, so existing
applications and libraries still need ``gopkg.in`` to resolve them to the
right repository and version. ``gopkg-k8s`` keeps that contract
available; the service is not a second package manager and does not replace
Go's module tooling.

What the service does
---------------------

For a request such as ``gopkg.in/yaml.v2``, the service:

1. maps the path to its GitHub repository and selects the newest branch or
   tag that matches the requested major version;
2. answers the Go tool's repository discovery request with ``go-import`` and
   ``go-source`` metadata, following the protocol described in `Finding a
   repository for a module path <https://go.dev/ref/mod#vcs-find>`_ in the
   Go documentation;
3. serves the selected version to Git over HTTP, relaying the transfer from
   GitHub; and
4. renders a package page with source, API, and version links for browsers.

.. mermaid::

     flowchart TD
     source["Go import<br/>gopkg.in/yaml.v2"]
     repository["Map to GitHub<br/>go-yaml/yaml"]
     version["Select the newest v2 tag"]
     package["Serve the source to the Go tool"]

     source --> repository --> version --> package

The importing code keeps its ``gopkg.in`` path; the standard Go and Git
clients perform the download.

What the charm adds
-------------------

``gopkg-k8s`` is the operational layer of the HTTP application:
the service is packaged as a rock, Juju deploys the
charm on Kubernetes, and the charm manages the workload's configuration and
integrations. Two operational facts follow from the service's job:

- The workload reaches GitHub over HTTPS to read repository references and
  to relay source transfers, so the cluster must allow that outbound access.
- The hostname the service writes into ``go-import`` metadata and package
  links must be the public name that clients use. The ``hostname``
  option is described in :ref:`charm-configuration` and
  :ref:`configure-hostname-and-check-go-import`.

See :doc:`Juju, charms, and rocks <juju-charms-and-rocks>` for the packaging
and orchestration concepts, and :doc:`Ingress <ingress>` for how requests
reach the service from outside the cluster.

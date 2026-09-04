gopkg charm
===========

**gopkg-charmed operates the gopkg.in versioned Go import service on
Kubernetes.** It is a `Juju <https://juju.is/>`_
`charm <https://documentation.ubuntu.com/juju/3.6/reference/charm/>`_ that
packages the service, deploys it, configures its public hostname, and connects
it to ingress.

The charm is useful to platform engineers, DevOps engineers, and SRE teams who
need to operate ``gopkg.in`` reliably. It is also relevant to maintainers of Go
software that still imports packages through ``gopkg.in`` paths.

Go dependencies and versions
----------------------------

A Go program is organized into packages. A module groups one or more related
packages and records their dependencies in a ``go.mod`` file. When a developer
runs a command such as ``go get`` or ``go build``, the Go tool reads module
paths and versions, downloads the required source, and verifies the downloaded
content. Module versions normally correspond to tags in a source repository,
such as ``v1.2.3``.

Modern Go modules also encode incompatible major versions in module paths. For
example, version 2 of a module commonly uses a path ending in ``/v2``. This
allows a program to use different major versions without silently replacing
one incompatible API with another.

Why gopkg.in exists
-------------------

``gopkg.in`` introduced stable, major-version-specific import paths before Go
modules provided their current versioning model. An import such as
``gopkg.in/yaml.v2`` asks for major version 2 of the ``yaml`` repository while
allowing that major series to receive compatible minor and patch updates.

Go modules now solve version selection for new module-based projects, but they
do not remove import paths already published in source code and ``go.mod``
files. Those paths are part of the package's identity. Existing applications
and libraries therefore still need ``gopkg.in`` to resolve their imports to
the correct source repository and version. This application keeps that
established contract available; it is not a second package manager and does
not replace Go's module tooling.

What the application does
-------------------------

For each supported request, the Go service performs the following steps:

1. It parses the ``gopkg.in`` path into a repository owner, repository name,
    requested major version, and optional package subpath.
2. It maps that path to its source repository on GitHub.
3. It reads the repository's Git branches and tags and selects the newest
    reference matching the requested major version.
4. For a Go discovery request ending in ``?go-get=1``, it returns
    ``go-import`` and ``go-source`` metadata that tells the Go tool where to
    fetch the source.
5. For a Git smart-HTTP request, it exposes the selected reference as the
    repository head and proxies the source transfer from GitHub.
6. For a browser request, it renders a package page with source, API, and
    available-version information.

For example, the service resolves ``gopkg.in/yaml.v2`` to the corresponding
GitHub repository and the latest compatible version in its ``v2`` series. The
calling developer continues to use the stable ``gopkg.in`` import path while
the standard Go and Git clients perform the download.

Here is that example from import statement to downloaded source:

.. mermaid::

     flowchart TD
     source["Go import<br/>gopkg.in/yaml.v2"]
     repository["Map to GitHub<br/>go-yaml/yaml"]
     version["Select v2 tag"]
     package["Fetch package"]

     source -->|?go-get=1| repository --> version --> package

What ``?go-get=1`` means
~~~~~~~~~~~~~~~~~~~~~~~~

The ``?`` starts the query part of the URL. ``go-get`` is the parameter name,
and ``1`` tells gopkg.in that the Go command is discovering where to fetch the
package source. The Go command adds this parameter automatically; it does not
appear in an ``import`` statement.

For this request, gopkg.in returns a small HTML page containing ``go-import``
and ``go-source`` metadata instead of the normal package page. The metadata
identifies the Git import root and source location that the Go command should
use.

The ``go-import`` response tells the Go tool that ``gopkg.in/yaml.v2`` is a
Git import root. The service then makes the selected GitHub version available
through that stable import root. The source code still imports
``gopkg.in/yaml.v2``; it does not need to change to a GitHub URL.

What the charm adds
-------------------

The application is the HTTP service described above. ``gopkg-charmed`` is its
operational layer. Like other Juju charms, it supports repeatable deployment,
configuration, integration, and lifecycle management. In particular, the
charm provides:

- deployment of the OCI-packaged Go workload on Kubernetes
- runtime configuration of the hostname rendered in import metadata and links
- integration with an ingress charm for external HTTP routing and TLS
  termination
- a health endpoint for Kubernetes and operational checks
- Juju status and lifecycle handling through the
    `Canonical 12-factor charm framework <https://canonical.com/juju/docs/charmcraft/stable/howto/manage-web-app-charms/>`_

The charm can be deployed to Kubernetes environments supported by Juju, from
`MicroK8s <https://microk8s.io/>`_ for local development to
`Charmed Kubernetes <https://ubuntu.com/kubernetes>`_ and public-cloud
Kubernetes offerings. It gives operators a consistent Juju interface while
preserving the import-path behavior expected by existing Go consumers.

In this documentation
---------------------

Use the navigation sections below to find task-oriented guides and reference
material.

How this documentation is organized
-----------------------------------

The structure follows a four-part documentation framework:

- Tutorials for end-to-end guided examples
- How-to guides for practical tasks
- Reference for configuration and interfaces
- Explanation for architecture and design context

Project and community
---------------------

The project source code and issue tracker are hosted on GitHub:

- https://github.com/canonical/gopkg-charmed

Get involved
~~~~~~~~~~~~

Contributions are welcome. Start with repository contribution and compliance
guides in the project root.

Releases and support
~~~~~~~~~~~~~~~~~~~~

Release notes are published under the ``release-notes`` section in this
documentation set.

Governance and policies
~~~~~~~~~~~~~~~~~~~~~~~

Governance and security policies live in the repository root files.

.. toctree::
    :hidden:
    :maxdepth: 1

    tutorials/index
    how-to/index
    reference/index
    explanation/index

.. toctree::
    :hidden:
    :maxdepth: 1

    release-notes/index
    contribute/index

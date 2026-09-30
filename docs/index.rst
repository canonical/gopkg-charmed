.. meta::
    :description: Operate the gopkg.in versioned Go import service on Kubernetes with the gopkg-k8s Juju charm.

gopkg charm
===========

``gopkg-k8s`` is a `Juju <https://canonical.com/juju>`_ `charm
<https://canonical.com/juju/docs/juju-cli/3.6/reference/charm/>`_ that
operates the ``gopkg.in`` versioned Go import service on Kubernetes.

The service ships as a rock, a container image built with Rockcraft. Juju
deploys the charm, and the charm runs that image, configures the public
hostname the service advertises, and connects it to ingress. Like any Juju
charm, it supports repeatable deployment, configuration, integration, and
lifecycle management, on Kubernetes platforms from `MicroK8s
<https://canonical.com/microk8s>`_ for local development to `Charmed
Kubernetes <https://ubuntu.com/kubernetes>`_ and public-cloud Kubernetes
offerings.

``gopkg.in`` gives Go programs stable, major-version-specific import paths:
``gopkg.in/yaml.v2`` resolves to the newest v2 tag of the ``go-yaml/yaml``
repository. Canonical maintains this charm to run the public ``gopkg.in``
service. The service writes the configured hostname into its
``go-import`` metadata, so a deployment serves imports of that hostname, not
of ``gopkg.in``: code that already imports ``gopkg.in/...`` keeps using the
public service. Operators use their own copy to mirror ``gopkg.in`` inside a network
that cannot reach it, or to offer versioned import paths for GitHub
repositories under their own domain.

In this documentation
---------------------

.. list-table::
   :header-rows: 1

   * -
     -
   * - Get started
     - :ref:`Deploy and verify gopkg-k8s on Kubernetes <deploy-and-verify-on-kubernetes>`
   * - Deployment
     - :ref:`Configure ingress <configure-ingress>`
       | :ref:`Configure hostname <configure-hostname-and-check-go-import>`
       | :ref:`Set up production DNS <configure-ingress-dns>`
       | :ref:`Charm configuration <charm-configuration>`
       | :ref:`Platforms and prerequisites <platforms-and-prerequisites>`
   * - Operations
     - :ref:`Integrate with the Canonical Observability Stack <integrate-with-cos>`
       | :ref:`Troubleshoot deployment issues <troubleshoot-deployment>`
       | :ref:`Alert rules <integrations-alert-rules>`
   * - Versioned import paths
     - :ref:`Why gopkg.in exists <gopkg-service-why>`
       | :ref:`What the service does <gopkg-service-what-it-does>`
       | :ref:`Fetch a module with the Go tool <tutorial-fetch-module>`
       | :ref:`How a deployment differs from gopkg.in <gopkg-service-differences>`
   * - Integrations
     - :ref:`Integration endpoints <integrations>`
       | :ref:`Metrics <integrations-metrics>`
       | :ref:`Logs <integrations-logs>`
   * - Design
     - :ref:`How a request reaches the workload <ingress-request-path>`
       | :ref:`The two hostname settings <ingress-two-hostnames>`
       | :ref:`What the charm adds <gopkg-service-what-the-charm-adds>`
   * - Security
     - :ref:`Enable HTTPS <configure-ingress-https>`
       | :ref:`Where TLS terminates <ingress-tls>`
       | :ref:`Keep the metrics endpoint off the public hostname <cos-metrics-port>`
   * - Development
     - :ref:`Set up a development environment <set-up-a-development-environment>`
       | :ref:`Improve the code <improve-code>`
       | :ref:`Improve the documentation <improve-documentation>`
       | :ref:`CI workflows <ci-workflows>`

How this documentation is organized
-----------------------------------

This documentation uses the `Diátaxis <https://diataxis.fr/>`_ documentation
structure.

- The :ref:`Tutorial <tutorials>` takes you step-by-step through a complete
  deployment of ``gopkg-k8s``, from an empty machine to a Go program that
  fetches a module through it.
- :ref:`How-to guides <how-to-guides>` assume you have a deployment. Learn
  how to configure ingress and the hostname, connect observability, and
  troubleshoot.
- :ref:`Reference <reference>` provides the configuration options,
  integration endpoints, metrics, alert rules, and supported platforms.
- :ref:`Explanation <explanation>` covers what the ``gopkg.in`` service does
  for Go programs and how requests reach it through ingress.
- :ref:`Contribute <contribute>` covers building the charm and its
  documentation from source, and the tests that CI runs.
- :ref:`Release notes <release_notes_index>` hold the release history.

Contributing to this documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Documentation is an important part of this project, and it takes the same
open source approach as the code. Community contributions, suggestions, and
constructive feedback are welcome; see :ref:`contribute` for how to get
started. If a topic you need is missing, please `file a bug
<https://github.com/canonical/gopkg-charmed/issues>`_.

Project and community
---------------------

``gopkg-k8s`` is a member of the Ubuntu family. It is an open source
project that warmly welcomes community projects, contributions, suggestions,
fixes, and constructive feedback.

Governance and policies
~~~~~~~~~~~~~~~~~~~~~~~

- `Code of conduct <https://ubuntu.com/community/docs/ethos/code-of-conduct>`_
- `Security policy <https://github.com/canonical/gopkg-charmed/blob/main/SECURITY.md>`_

Get involved
~~~~~~~~~~~~

- `Get support <https://discourse.charmhub.io/>`_
- `Join our online chat <https://matrix.to/#/#charmhub-charmdev:ubuntu.com>`_
- `Report an issue <https://github.com/canonical/gopkg-charmed/issues>`_
- :ref:`Contribute <contribute>`

Thinking about using ``gopkg-k8s`` for your next project? `Get in touch
<https://matrix.to/#/#charmhub-charmdev:ubuntu.com>`_!

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

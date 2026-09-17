.. meta::
    :description: Operate the gopkg.in versioned Go import service on Kubernetes with the gopkg-charmed Juju charm.

gopkg charm
===========

``gopkg-charmed`` is a `Juju <https://canonical.com/juju>`_ `charm
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

The charm is useful to platform engineers, DevOps engineers, and SRE teams
who need to operate ``gopkg.in`` reliably, and to maintainers of Go software
that depends on ``gopkg.in`` import paths.

In this documentation
---------------------

.. grid:: 1 1 2 2

   .. grid-item-card:: Tutorial
      :link: tutorials
      :link-type: ref

      **Start here**: build, deploy, and verify ``gopkg-charmed`` on
      Kubernetes from a fresh environment.

   .. grid-item-card:: How-to guides
      :link: how-to-guides
      :link-type: ref

      **Step-by-step guides** for configuring ingress and the hostname,
      running the test suite, and troubleshooting.

.. grid:: 1 1 2 2
   :reverse:

   .. grid-item-card:: Reference
      :link: reference
      :link-type: ref

      **Technical information**: configuration options, supported platforms
      and prerequisites, and CI workflows.

   .. grid-item-card:: Explanation
      :link: explanation
      :link-type: ref

      **Discussion and clarification** of how gopkg.in resolves imports and
      how rocks, charms, Juju, and ingress fit together.

How this documentation is organized
-----------------------------------

This documentation uses the `Diátaxis <https://diataxis.fr/>`_ documentation
structure.

- The :ref:`Tutorial <tutorials>` takes you step-by-step through a complete
  deployment of ``gopkg-charmed``.
- :ref:`How-to guides <how-to-guides>` cover preparing an environment,
  configuring the charm, testing it, and troubleshooting it.
- :ref:`Reference <reference>` provides the configuration options, supported
  platforms, and CI behavior.
- :ref:`Explanation <explanation>` includes topic overviews, background and
  context, and detailed discussion.
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

``gopkg-charmed`` is a member of the Ubuntu family. It is an open source
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

Thinking about using ``gopkg-charmed`` for your next project? `Get in touch
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

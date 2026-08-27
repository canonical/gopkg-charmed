.. _architecture-and-operations:

Architecture and operations overview
====================================

What gopkg-charmed manages
--------------------------

gopkg-charmed is a Kubernetes charm that runs the ``gopkg.in`` workload and
manages it through Juju operations.

The charm controls:

- workload lifecycle
- configuration delivery through charm config
- integrations such as ingress and observability endpoints

Platform model
--------------

The deployment model is intentionally architecture-aware and supports both
``amd64`` and ``arm64``.

The key operational rule is that Juju model constraints must match node
architecture. If they do not match, pods can remain pending.

Ingress and hostname responsibilities
-------------------------------------

There are two separate hostname responsibilities:

- ingress ``service-hostname`` controls routing host matching
- charm ``hostname`` config controls workload-rendered host metadata

Keeping them separate enables flexible routing while preserving predictable
application metadata behavior.

Why tutorial validation exists in CI
------------------------------------

Tutorials are only useful if they stay executable in practice.

For this reason, tutorial-related documentation changes trigger integration
smoke validation through CI. This gives fast feedback when deployment guidance
and real charm behavior drift apart.

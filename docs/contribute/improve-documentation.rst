.. _improve-documentation-and-tutorial-tests:
.. _improve-documentation:

.. meta::
   :description: Build, preview, and validate gopkg-charmed documentation and executable examples locally.

Improve the documentation
=========================

Use this path for changes under ``docs/``. You can build and check the
documentation on Linux or macOS without installing Juju, MicroK8s, Rockcraft,
or Charmcraft.

Prerequisites
-------------

You need Git, Make, and Python 3 with ``venv``. On Ubuntu, run:

.. code-block:: bash

   sudo apt update
   sudo apt install --yes git make python3 python3-venv

Clone the repository if you do not already have a checkout, then install the
pinned documentation dependencies:

.. code-block:: bash

   cd ~
   git clone https://github.com/canonical/gopkg-charmed.git gopkg-charm
   cd gopkg-charm
   make -C docs install

This creates an isolated environment in ``docs/.venv``.

Understand the documentation layout
-----------------------------------

Choose the directory that matches the reader's need:

- ``docs/tutorials/`` provides guided learning.
- ``docs/how-to/`` gives goal-oriented procedures.
- ``docs/reference/`` records facts and settings.
- ``docs/explanation/`` explains concepts and design.
- ``docs/contribute/`` supports contributors.

Preview your change
-------------------

Build and preview the site:

.. code-block:: bash

   cd ~/gopkg-charm
   make -C docs html
   make -C docs run

Open ``http://127.0.0.1:8000``. Stop the preview with ``Ctrl+C``.

Run documentation checks
------------------------

Before opening a pull request, run:

.. code-block:: bash

   cd ~/gopkg-charm
   make -C docs html
   make -C docs vale
   make -C docs spelling
   make -C docs woke

Run ``make -C docs linkcheck`` when you add or change links.

Test executable documentation
-----------------------------

The **Documentation tests** workflow extracts shell commands from tutorials and
how-to guides and runs them on a bare Ubuntu system with Spread. The guides'
own commands install the tools and provision the environment, so the test
covers the same path a reader follows.

When you edit an executable command:

1. Keep it complete and safe to copy.
2. Add a check that fails when the expected result is missing.
3. Use ``SPREAD SKIP`` only for genuinely interactive steps, such as entering
   a Multipass VM or watching ``juju status``.
4. Use an invisible ``SPREAD`` block for a finite CI alternative.
5. Where the reader must log out and back in, emit the sentinel line
   ``# spread-session-break`` from an invisible ``SPREAD`` block; the test
   harness starts a fresh login shell there.

Scenarios live in ``tests/spread/documentation/``; each task runs its guides
in prerequisite order through ``tests/spread/documentation/run-docs.sh``.
When moving a tested page, update its task and
``.github/workflows/documentation-tests.yml``.

You do not need a local Juju environment for prose-only changes. If your new
command builds, deploys, or changes the running service, also follow
:ref:`improve-code` and validate the affected runtime path.

See :ref:`ci-workflows` for the complete CI behavior.
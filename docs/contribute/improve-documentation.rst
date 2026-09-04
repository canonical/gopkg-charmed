.. _improve-documentation-and-tutorial-tests:
.. _improve-documentation:

Improve the documentation
=========================

Use this path for changes under ``docs/``. You can build and check the
documentation on Linux or macOS without installing Juju, MicroK8s, Rockcraft,
or Charmcraft.

Prepare the documentation environment
-------------------------------------

You need Git, Python 3 with ``venv``, and Make. On Ubuntu, install them with:

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

The final command creates ``docs/.venv``. It does not modify your global Python
environment.

Understand the documentation layout
-----------------------------------

The documentation follows the Diataxis structure:

- ``docs/tutorials/`` teaches through a complete learning experience.
- ``docs/how-to/`` gives goal-oriented procedures.
- ``docs/reference/`` records facts, interfaces, and supported settings.
- ``docs/explanation/`` provides background and design context.
- ``docs/contribute/`` helps contributors work on this repository.

Choose the section based on what the reader is trying to accomplish, not on
which source file or component the page describes.

Preview your change
-------------------

Build the site once:

.. code-block:: bash

   cd ~/gopkg-charm
   make -C docs html

The build succeeds without warnings and writes the rendered site to
``docs/_build/``. To rebuild and serve the site while editing, run:

.. code-block:: bash

   make -C docs run

Open ``http://127.0.0.1:8000`` and stop the server with ``Ctrl+C`` when you are
finished.

Run documentation checks
------------------------

Before opening a pull request, run:

.. code-block:: bash

   cd ~/gopkg-charm
   make -C docs html
   make -C docs vale
   make -C docs spelling
   make -C docs woke

These commands check the Sphinx build, style, spelling, and inclusive language.
Run ``make -C docs linkcheck`` as well when you add or change links.

Test executable documentation
-----------------------------

Commands in ``docs/tutorials/`` and ``docs/how-to/`` are part of the tested
product experience. The **Documentation tests** workflow extracts shell code
blocks with ``opcli tutorial expand`` and executes them through Spread in a
provisioned Ubuntu environment.

When you edit an executable command:

1. Keep the command complete and safe to copy and paste.
2. Add a verification command whose exit status is nonzero when the expected
   result is missing.
3. Keep commands in dependency order when a scenario combines multiple guides.
4. Use ``SPREAD SKIP`` only for interactive commands or setup already performed
   by the CI provisioner.
5. Use an invisible ``SPREAD`` block when CI needs a finite equivalent for an
   interactive command.

The scenarios live in ``tests/spread/documentation/``. If you move a tested
page, update its Spread task and the path filters in
``.github/workflows/documentation-tests.yml``.

You do not need a local Juju environment for prose-only changes. If your new
command builds, deploys, or changes the running service, also follow
:ref:`improve-code` and validate the affected runtime path.

Before you open a pull request
------------------------------

Confirm that:

- the page is in the correct Diataxis section
- a new page appears in the appropriate ``index.rst`` toctree
- commands state where they run and include an expected result
- local documentation checks pass
- the **Documentation tests** workflow passes for executable tutorial or
  how-to changes

See :ref:`ci-workflows` for the complete CI behavior.
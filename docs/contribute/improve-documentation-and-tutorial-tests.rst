.. _improve-documentation-and-tutorial-tests:

Improve documentation and tutorial tests
========================================

Before you start
----------------

For documentation-only changes, you need Python 3, ``venv``, and ``make``.
The documentation environment is installed by the commands in
:ref:`local-documentation-validation` below.

To run commands that build, deploy, or test the charm, first follow
:ref:`Set up a local Linux environment <set-up-a-local-linux-environment>`.
That guide installs the required Linux VM, MicroK8s, Juju, Rockcraft,
Charmcraft, and tox environment.

To set up and run the complete charm integration suite after preparing the
environment, follow :ref:`Run the full Juju integration suite locally
<full-integration-suite-local>`.

Documentation quality standards
-------------------------------

When contributing docs:

- assume the reader is new to the project
- provide complete commands, not partial snippets
- include expected output or verification steps
- keep architecture guidance explicit for ``amd64`` and ``arm64``

.. _local-documentation-validation:

Test the documentation locally
------------------------------

Run these checks before opening a pull request:

.. code-block:: bash

   cd ~/gopkg-charm
   make -C docs install
   make -C docs html
   make -C docs vale
   make -C docs spelling
   make -C docs woke

``html`` builds the documentation and fails on Sphinx warnings. The remaining
commands check style, spelling, and inclusive language. The generated site is
available in ``docs/_build/``.

If a deleted or renamed page still appears in a local preview, remove stale
generated files and rebuild:

.. code-block:: bash

   cd ~/gopkg-charm
   make -C docs clean-doc
   make -C docs html

Documentation command tests
---------------------------

The documentation test workflow uses ``opcli tutorial expand`` from
``canonical/charm-ci`` to extract shell commands directly from tutorial and
how-to RST code blocks. Spread runs each generated script in a provisioned
Ubuntu environment. Changing an executable documentation command therefore
changes the CI test automatically.

These tests require a provisioned Ubuntu environment because the documented
commands build artifacts and deploy applications to MicroK8s. They run
automatically on a pull request when relevant tutorial, how-to, Spread, charm,
or rock files change. You can also run the **Documentation tests** workflow
manually from the repository's GitHub Actions page.

See :ref:`ci-workflows` for the workflow behavior and job selection. The
scenario definitions are in ``tests/spread/documentation/``, and the workflow
entry point is ``.github/workflows/documentation-tests.yml``.

Related how-to guides can form one scenario. Keep them in dependency order;
for example, the hostname scenario extracts environment setup, local
deployment, and hostname configuration commands into one shell script.

Wrap interactive commands or commands already performed by the CI provisioner
in ``SPREAD SKIP`` markers. Use an invisible ``SPREAD`` block for a finite CI
equivalent when needed. Keep verification commands self-checking with nonzero
exit statuses on failure.

Which test path to use
----------------------

- For prose or navigation changes, run :ref:`local-documentation-validation`.
- For executable tutorial or how-to commands, run the local checks and the
   **Documentation tests** GitHub Actions workflow.
- For charm behavior, prepare Linux with
   :ref:`Set up a local Linux environment <set-up-a-local-linux-environment>`,
   then :ref:`run the full Juju integration suite locally
   <full-integration-suite-local>`.

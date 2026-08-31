.. _improve-documentation-and-tutorial-tests:

Improve documentation and tutorial tests
========================================

Documentation quality standards
-------------------------------

When contributing docs:

- assume the reader is new to the project
- provide complete commands, not partial snippets
- include expected output or verification steps
- keep architecture guidance explicit for ``amd64`` and ``arm64``

Local validation
----------------

Run these checks before opening a pull request:

.. code-block:: bash

   cd ~/gopkg-charm
   make -C docs install
   make -C docs html
   make -C docs spelling
   make -C docs woke

Tutorial alignment with integration tests
-----------------------------------------

The tutorial smoke workflow uses ``opcli tutorial expand`` from
``canonical/charm-ci`` to extract shell commands directly from the tutorial's
RST code blocks. Spread runs the generated script in a provisioned Ubuntu
environment. Changing an executable tutorial command therefore changes the CI
test automatically.

Wrap interactive commands or commands already performed by the CI provisioner
in ``SPREAD SKIP`` markers. Use an invisible ``SPREAD`` block for a finite CI
equivalent when needed. Keep verification commands self-checking with nonzero
exit statuses on failure.

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

   make -C docs install
   make -C docs html
   make -C docs spelling
   make -C docs woke

Tutorial alignment with integration tests
-----------------------------------------

Tutorial deployment instructions are validated by integration smoke checks in
CI through ``tutorial-integration-smoke.yml`` and tutorial-focused integration
tests.

If you change deployment commands in tutorials, update the associated
integration test intent and assertions so docs and deploy reality stay aligned.

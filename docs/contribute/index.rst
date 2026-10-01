.. _contribute:

.. meta::
	:description: Learn how to contribute to the documentation or code for gopkg-k8s.

Contribute
==========

Contributions can change the documentation, the Go service, the charm, the
rock, or several of these areas. Choose the path that matches your change, and
follow both when code and documentation change together. On either path,
:ref:`ci-workflows` describes what CI runs on each change.

Documentation contributions
---------------------------

For prose, navigation, examples, tutorials, and how-to guides:

- :ref:`improve-documentation`: install the documentation tools, preview a
  change, and run the documentation checks and tests.

Prose-only changes need no local Juju environment. If a documentation command
builds, deploys, or changes the running service, also follow the code path,
starting with :ref:`set-up-a-development-environment`, to validate it.

Code contributions
------------------

For the Go service, charm code, rock or charm recipes, and integration tests:

- :ref:`set-up-a-development-environment`: prepare a VM with the tools that
  build, test, and deploy ``gopkg-k8s`` from source. Start here.
- :ref:`improve-code`: run the tests, then build and deploy your change.
- :ref:`Run the integration suite locally <full-integration-suite-local>`: run
  the Juju integration suite by hand.
- :ref:`troubleshoot-development`: fix the failures that come up while
  building from source.

.. vale off

.. toctree::
	:hidden:
	:maxdepth: 1

	set-up-a-development-environment
	improve-documentation
	improve-code
	Run the integration suite locally <run-full-juju-integration-suite-locally>
	ci-workflows
	troubleshoot-development

.. vale on

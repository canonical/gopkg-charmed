.. _contribute:

Contribute
==========

Contributions can change the documentation, the Go service, the charm, the
rock, or more than one of these areas. Start with the path that matches your
change; you do not need the full deployment environment for every contribution.

Choose a contribution path
--------------------------

Use :ref:`improve-documentation` for prose, navigation, examples, tutorials,
and how-to guides. This path starts with a small Python and Sphinx environment.
Executable commands in tutorials and how-to guides receive additional tests in
CI.

Use :ref:`improve-code` for the Go service, charm code, rock or charm recipes,
and integration tests. This path uses a Linux, MicroK8s, and Juju environment
to run the fast tests, rebuild the rock and charm, and verify the deployed
service.

The paths are separate but connected. If a code change alters documented
behavior, follow both paths: validate the implementation first, then update and
build the relevant documentation. If a documentation example changes how the
application is built or operated, use the code path to validate that command in
a real environment.

.. toctree::
	:maxdepth: 1

	improve-documentation
	improve-code

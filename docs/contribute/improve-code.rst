.. _improve-code:

.. meta::
   :description: Set up and run Go, charm, and Juju integration tests for code changes to gopkg-k8s.

Improve the code
================

Use this path for changes to the Go service, charm, rock, or integration tests.
Run every test below for each code contribution. The final test rebuilds and
deploys the rock and charm.

Prerequisites
-------------

Complete :ref:`Set up a local Linux environment
<set-up-a-local-linux-environment>` first.

The Go service is under ``app/``. ``app/rockcraft.yaml`` packages it as a rock,
and the charm under ``app/charm/`` operates that image with Juju. See
:ref:`Juju charms and rocks <juju-charms-and-rocks>` for background.

Run all tests
-------------

Run the Go checks:

.. code-block:: bash

   cd ~/gopkg-charm/app
   test -z "$(gofmt -l .)"
   go vet ./...
   go build ./...
   go test -race ./...

Next, run the charm checks:

.. code-block:: bash

   cd ~/gopkg-charm/app/charm
   tox -e lint,unit,static

Finally, rebuild, deploy, and test the rock and charm:

.. code-block:: bash

   cd ~/gopkg-charm
   app/charm/tests/integration/run_full_local_suite.sh

Success ends with ``Full local Juju integration suite completed``. For manual
steps, see :ref:`full-integration-suite-local`.

Build and deploy from source
----------------------------

The tutorial deploys the charm and its image from Charmhub. To try a change to
the service, the rock, or the charm by hand, build both locally and deploy the
result the same way. The recipes declare ``amd64`` and ``arm64``, so this path
works on either architecture, unlike the published charm.

Build the rock. ``app/rockcraft.yaml`` uses Rockcraft's Go framework extension,
which builds the Go module and sets up the runtime; the extension is marked
experimental, so the environment variable opts in to it. The build runs inside
an LXD instance and fetches packages from the Ubuntu archive, so the first
build takes several minutes; if it fails with a network error from the
archive, run the command again:

.. code-block:: bash

   cd ~/gopkg-charm/app
   ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true rockcraft pack

It produces ``gopkg_0.1_<architecture>.rock`` in ``app/``. Kubernetes pulls
images from a registry, not from files, so push the rock to the local registry
that the MicroK8s ``registry`` add-on runs on port 32000, and check that the
registry lists the tag. ``rockcraft.skopeo`` is the copy of ``skopeo`` inside
the Rockcraft snap; its flags allow the plain-HTTP, unauthenticated local
registry:

.. code-block:: bash

   microk8s kubectl rollout status deployment/registry \
     -n container-registry --timeout=15m
   rockcraft.skopeo copy --insecure-policy --dest-tls-verify=false --dest-no-creds \
     oci-archive:gopkg_0.1_$(dpkg --print-architecture).rock \
     docker://localhost:32000/gopkg:0.1
   curl --fail --silent --show-error \
     http://localhost:32000/v2/gopkg/tags/list | grep -F '"0.1"'

Build the charm with Charmcraft's Go framework extension, the counterpart of
the Rockcraft one:

.. code-block:: bash

   cd ~/gopkg-charm/app/charm
   CHARMCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS=true charmcraft pack
   ls -1 gopkg-k8s_$(dpkg --print-architecture).charm

Deploy the local charm with the image you pushed. Use a fresh model, or
destroy the tutorial's first. The model constraint schedules the pods on your
machine's architecture, which the rock you built requires:

.. code-block:: bash

   juju add-model gopkg-k8s
   juju set-model-constraints arch=$(dpkg --print-architecture)
   juju deploy ./gopkg-k8s_$(dpkg --print-architecture).charm gopkg-k8s \
     --resource app-image=localhost:32000/gopkg:0.1

From here the tutorial applies unchanged from :ref:`deploy-and-verify-on-kubernetes`:
deploy and integrate the ingress integrator, set both hostname settings,
and verify the service.

Update the documentation
------------------------

Update the documentation when a code change affects configuration, deployment,
commands, or user-visible behavior. Follow :ref:`improve-documentation` for
those changes.
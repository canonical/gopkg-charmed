.. _upgrade-the-charm:

.. meta::
   :description: Move a gopkg-k8s deployment to a newer charm revision with juju refresh, wait for Juju to replace the workload, and verify the service through ingress.

How to upgrade
==============

A new revision of ``gopkg-k8s`` on Charmhub carries the charm and the
``app-image`` resource it runs, so one ``juju refresh`` upgrades both. The
service keeps no persistent state, so there is nothing to back up or migrate.
What an upgrade costs is availability: Juju replaces the pod, and the ingress
keeps sending requests to the old pod's address until the new unit publishes
its own.

This guide assumes that ``gopkg-k8s`` and ``nginx-ingress-integrator``
are deployed and integrated, with
the integrator's ``service-hostname`` exported as ``INGRESS_HOST``:

.. code-block:: bash

   export INGRESS_HOST=gopkg.example.com

Check the current and the available revision with:

.. code-block:: bash

   juju status gopkg-k8s
   juju info gopkg-k8s

The ``Rev`` column of ``juju status`` is the revision the deployment runs, and
``Channel`` is the channel it follows:

.. terminal::
   :output-only:

   App        Version  Status  Scale  Charm      Channel      Rev  Address        Exposed  Message
   gopkg-k8s           active      1  gopkg-k8s  latest/edge    4  10.152.183.31  no

``juju info`` ends with every channel of the charm and the revision each one
offers, in parentheses. A higher number on the deployment's channel means an
upgrade is available.

Note the current revision in case you need to roll back the upgrade.

.. SPREAD
   previous=$(juju status gopkg-k8s --format=yaml | awk '/charm-rev:/ { print $2 - 1; exit }')
   juju refresh gopkg-k8s --revision "${previous}"
   sleep 30
   juju wait-for application gopkg-k8s \
     --query='status=="active"' --timeout=15m
   microk8s kubectl -n gopkg-k8s rollout status statefulset/gopkg-k8s --timeout=15m
.. SPREAD END

Upgrade
-------

Move the application to the newest revision of its channel:

.. code-block:: bash

   juju refresh gopkg-k8s

Juju names the revision it added:

.. terminal::
   :output-only:

   Added charm-hub charm "gopkg-k8s", revision 5 in channel latest/edge, to the model

If the deployment already runs that revision, it prints ``charm "gopkg-k8s":
already up-to-date`` instead and changes nothing. To follow another channel,
add ``--channel``, for example ``--channel latest/stable``; to move to one
particular revision, add ``--revision``.

Juju replaces the pod with the new revision's image. Wait until the
application reports ``active`` again using ``juju status``.

.. SPREAD
   sleep 30
   juju wait-for application gopkg-k8s \
     --query='status=="active"' --timeout=15m
   microk8s kubectl -n gopkg-k8s rollout status statefulset/gopkg-k8s --timeout=15m
.. SPREAD END

Verify the upgrade
------------------

Check that the deployment runs the new revision:

.. code-block:: bash

   juju status gopkg-k8s

The ``Rev`` column shows the revision that ``juju refresh`` named.

.. SPREAD
   current=$(juju status gopkg-k8s --format=yaml | awk '/charm-rev:/ { print $2; exit }')
   test "${current}" -gt "${previous}"
.. SPREAD END

Then check the service through ingress. After Juju replaces the pod, the
integrator continues routing requests to the old address until the new unit
publishes its address. This can take up to four minutes, during which requests
fail with ``502``, ``503``, or ``504``. Query until the health check answers
(the loop gives up after ten minutes):

.. code-block:: bash

   timeout 600 bash -c '
     until curl --fail --silent --show-error \
         http://${INGRESS_HOST}/health-check \
         --resolve "${INGRESS_HOST}:80:127.0.0.1" | grep -Fx ok; do
       sleep 5
     done
   '

The output is ``ok``. Finally, send the query the Go tool sends, to confirm
that the upgraded service answers package requests:

.. code-block:: bash

   curl --fail --silent --show-error --retry 30 --retry-delay 2 \
     --retry-all-errors \
     "http://${INGRESS_HOST}/yaml.v2?go-get=1" \
     --resolve ${INGRESS_HOST}:80:127.0.0.1 | grep go-import

The output is the ``go-import`` meta tag. If the loop gives up or a check
fails, see :ref:`troubleshoot-deployment`.

Roll back an upgrade
--------------------

If you need to roll back, refresh to the revision you noted at the
start:

.. SPREAD SKIP

.. code-block:: bash

   juju refresh gopkg-k8s --revision <previous-revision>

.. SPREAD SKIP END

The application keeps following its channel: a later ``juju refresh`` without
options moves it to the channel's newest revision again.

If you deploy with the Terraform module in ``terraform/``, its ``revision``
variable pins a revision and ``null`` follows ``channel``; see the module's
``README.md``.

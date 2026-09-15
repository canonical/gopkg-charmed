.. _integrate-with-cos:

.. meta::
   :description: Connect gopkg-charmed to Prometheus, Loki, and Grafana, verify that its metrics are scraped, and keep the metrics endpoint off the public hostname.

How to integrate with the Canonical Observability Stack
=======================================================

``gopkg-charmed`` exposes Prometheus metrics, forwards its structured logs,
and ships a Grafana dashboard and alert rules. Integrate its
``metrics-endpoint``, ``logging``, and ``grafana-dashboard`` endpoints with
the Canonical Observability Stack (COS) to use them. For what each endpoint
carries and the metrics and alert rules the charm provides, see
:ref:`integrations`.

These steps assume that ``gopkg-charmed`` and ``nginx-ingress-integrator``
are deployed and integrated, as they are after the deployment steps of
:ref:`deploy-and-verify-on-kubernetes` and before its clean-up section. They
deploy the three COS charms into the same model, which is enough to see the
integrations work locally. A production deployment keeps COS in its own
model and integrates through cross-model offers; the `COS documentation
<https://documentation.ubuntu.com/observability/>`_ describes that layout.

Deploy the observability charms
-------------------------------

.. code-block:: bash

   juju deploy prometheus-k8s --channel=2/stable --trust
   juju deploy loki-k8s --channel=2/stable --trust
   juju deploy grafana-k8s --channel=2/stable --trust

Integrate the endpoints
-----------------------

.. code-block:: bash

   juju integrate gopkg-charmed:metrics-endpoint prometheus-k8s:metrics-endpoint
   juju integrate gopkg-charmed:logging loki-k8s:logging
   juju integrate gopkg-charmed:grafana-dashboard grafana-k8s:grafana-dashboard

Wait until every application is active:

.. SPREAD SKIP

.. code-block:: bash

   juju status --relations --watch 2s

.. SPREAD SKIP END

.. SPREAD
   for application in gopkg-charmed prometheus-k8s loki-k8s grafana-k8s; do
     juju wait-for application "${application}" \
       --query='status=="active"' --timeout=20m
   done
.. SPREAD END

Verify that Prometheus scrapes the service
------------------------------------------

Prometheus scrapes ``/metrics`` on the application port of every unit. Ask
its API for the ``up`` series of the application; a value of ``1`` means the
last scrape succeeded. Reach the API through the Kubernetes Service that Juju
maintains for ``prometheus-k8s``. Its address is the one ``juju status``
shows for the application, and it survives pod replacement, which the COS
charms trigger shortly after they first report active, when they set
resource limits on their own pods. The loop retries until the first scrape
completes and gives up after ten minutes:

.. code-block:: bash

   export PROMETHEUS_IP=$(microk8s kubectl -n gopkg-charmed get service \
     prometheus-k8s -o jsonpath='{.spec.clusterIP}')
   timeout 600 bash -c '
     until curl --silent --get "http://${PROMETHEUS_IP}:9090/api/v1/query" \
         --data-urlencode "query=up{juju_application=\"gopkg-charmed\"}" \
         | grep -F "\"1\"]"; do
       sleep 10
     done
   '

The output is a JSON document whose ``result`` entry ends in ``"1"``.

Logs and the dashboard need no extra steps. Every request other than a
health check produces one JSON log record, which Pebble forwards to Loki
with the Juju topology labels; in Grafana, the **Explore** view shows them
under the Loki data source when filtered by ``juju_application``. The
**gopkg Overview** dashboard and the Go framework's **Go Operator**
dashboard appear under **Dashboards**. The Grafana administrator password
comes from the ``get-admin-password`` action of ``grafana-k8s``.

Keep the metrics endpoint off the public hostname
-------------------------------------------------

By default the metrics endpoint shares the application port, so ingress
publishes it at ``/metrics`` on the public hostname. Move it to a port that
ingress does not route. The charm passes the new port to the service, which
opens a second listener for the metrics path only, and updates the scrape
job:

.. code-block:: bash

   juju config gopkg-charmed metrics-port=9102

Confirm that Prometheus scrapes the new port, then that the public hostname
no longer serves metrics. The ``up`` series cannot tell the ports apart,
because the Prometheus charm rewrites its ``instance`` label to the Juju
topology, so ask the targets API instead: it lists the scrape URL and health
of every active target. The loop waits until the target whose URL ends in
``:9102/metrics`` reports ``up``:

.. code-block:: bash

   timeout 600 bash -c '
     until curl --silent "http://${PROMETHEUS_IP}:9090/api/v1/targets?state=active" \
         | grep --only-matching "\"scrapeUrl\":\"[^\"]*:9102/metrics\"[^}]*\"health\":\"up\""; do
       sleep 10
     done
   '
   export INGRESS_HOST=gopkg.example.com
   curl --silent --output /dev/null --write-out '%{http_code}\n' \
     http://${INGRESS_HOST}/metrics \
     --resolve ${INGRESS_HOST}:80:127.0.0.1 | grep -Fx 404

The first command prints the matching part of the target entry, from its
scrape URL to ``"health":"up"``; the second prints ``404``, because the
application answers its own not-found page for that path.

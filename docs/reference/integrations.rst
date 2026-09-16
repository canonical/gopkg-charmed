.. _integrations:

.. meta::
   :description: Reference the gopkg-k8s integration endpoints, the metrics, logs, dashboard, and alert rules the charm provides, and its observability options.

Integrations
============

The Go framework extension gives ``gopkg-k8s`` the endpoints below. To
connect the observability endpoints, follow :ref:`integrate-with-cos`; for
ingress, follow :ref:`configure-ingress`. The ``secret-storage`` peer relation
is internal to the extension. For how the extension implements these
endpoints, see :ref:`charmcraft:go-framework-extension-relations` and
:ref:`charmcraft:go-framework-extension-observability`.

.. list-table::
   :header-rows: 1
   :widths: 22 12 22 44

   * - Endpoint
     - Role
     - Interface
     - Carries
   * - ``ingress``
     - requires
     - ``ingress``
     - The service's address and port, so an ingress charm such as
       ``nginx-ingress-integrator`` routes external HTTP traffic to it.
   * - ``logging``
     - requires
     - ``loki_push_api``
     - The Loki endpoint. Pebble forwards the service's standard output,
       one JSON record per line, labelled with the Juju topology. The Loki
       alert rules travel over the same relation.
   * - ``metrics-endpoint``
     - provides
     - ``prometheus_scrape``
     - A scrape job for ``metrics-path`` on ``metrics-port`` of every unit,
       and the Prometheus alert rules.
   * - ``grafana-dashboard``
     - provides
     - ``grafana_dashboard``
     - The **gopkg Overview** dashboard and the extension's **Go Operator**
       dashboard.

Observability options
---------------------

``metrics-port`` (default ``8080``, the application port) and
``metrics-path`` (default ``/metrics``) are framework options that reach the
service as ``APP_METRICS_PORT`` and ``APP_METRICS_PATH``. When the port
differs from the application port, the service opens a second listener that
serves only the metrics path, which keeps the endpoint off the port that
ingress publishes. The path must be absolute and must not be ``/`` or
``/health-check``. See :ref:`charmcraft:go-framework-extension-config-options`
for every framework option.

Metrics
-------

Besides the standard Go runtime and process collectors, the service exposes
the following metrics. Label values are bounded: routes are a fixed set of
names, and import paths, repository names, client addresses, and error text
are never labels.

.. list-table::
   :header-rows: 1
   :widths: 40 22 38

   * - Metric
     - Labels
     - Meaning
   * - ``gopkg_http_requests_total``
     - ``method``, ``route``, ``status_code``
     - Requests handled, by route and response status.
   * - ``gopkg_http_request_duration_seconds``
     - ``method``, ``route``
     - Request latency histogram.
   * - ``gopkg_upstream_requests_total``
     - ``service``, ``operation``, ``result``
     - Calls to GitHub and godoc.org, by outcome.
   * - ``gopkg_upstream_request_duration_seconds``
     - ``service``, ``operation``
     - Upstream call latency histogram.
   * - ``gopkg_refs_cache_requests_total``
     - ``result``
     - Repository refs cache hits and misses.
   * - ``gopkg_refs_cache_entries``
     - none
     - Entries held in the in-memory refs cache.
   * - ``gopkg_refs_retries_total``
     - none
     - GitHub refs requests retried after a timeout.
   * - ``gopkg_git_upload_pack_bytes_total``
     - ``direction``
     - Bytes proxied for ``git-upload-pack`` requests and responses.

The ``route`` label takes one of ``health_check``, ``root_redirect``,
``go_get``, ``package_page``, ``git_info_refs``, ``git_upload_pack``, and
``not_found``.

Logs
----

The service writes one JSON record per line to standard output. Request
records carry ``method``, ``path``, ``route``, ``status_code``, and
``duration_ms``; health checks are not logged. Failures are recorded at
level ``ERROR``, and a fatal start-up or server error is logged as
``application stopped`` before the process exits.

Alert rules
-----------

The charm ships these rules in ``app/charm/cos_custom``. Prometheus and Loki
receive them through the integrations and evaluate them with the Juju
topology of the deployment.

- ``GopkgTargetDown`` (critical): a unit has not been scraped successfully
  for five minutes.
- ``GopkgHighServerErrorRatio`` (critical): more than 5% of requests return a
  5xx status for five minutes, under sustained traffic.
- ``GopkgHighRequestLatency`` (warning): the 95th percentile latency of the
  functional routes exceeds two seconds for ten minutes.
- ``GopkgGitHubFailureRatio`` (warning): more than 20% of GitHub operations
  fail for five minutes, under sustained traffic.
- ``GopkgApplicationStopped`` (critical, Loki): the process logged
  ``application stopped``.
- ``GopkgErrorLogSpike`` (warning, Loki): more than ten ``ERROR`` records in
  five minutes.

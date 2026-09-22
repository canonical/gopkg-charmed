// Copyright 2026 Canonical Ltd.
// See LICENSE file for licensing details.

package main

import (
	"errors"
	"fmt"
	"log/slog"
	"net"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/collectors"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// logger writes one JSON record per line to standard output. Under the charm,
// Pebble forwards standard output to Loki once the logging endpoint is
// integrated, and the shipped Loki alert rules parse these records.
var logger = slog.New(slog.NewJSONHandler(os.Stdout, nil))

// appMetrics holds the service's Prometheus collectors. Label values are
// bounded on purpose: routes are a fixed set of names, and import paths,
// repository names, client addresses and error strings are never labels.
type appMetrics struct {
	registry                *prometheus.Registry
	httpRequests            *prometheus.CounterVec
	httpRequestDuration     *prometheus.HistogramVec
	refsCacheRequests       *prometheus.CounterVec
	refsCacheEntries        prometheus.Gauge
	upstreamRequests        *prometheus.CounterVec
	upstreamRequestDuration *prometheus.HistogramVec
	refsRetries             prometheus.Counter
	uploadPackBytes         *prometheus.CounterVec
}

var applicationMetrics = newAppMetrics()

func newAppMetrics() *appMetrics {
	metrics := &appMetrics{
		registry: prometheus.NewRegistry(),
		httpRequests: prometheus.NewCounterVec(prometheus.CounterOpts{
			Name: "gopkg_http_requests_total",
			Help: "Total number of HTTP requests handled by gopkg.",
		}, []string{"method", "route", "status_code"}),
		httpRequestDuration: prometheus.NewHistogramVec(prometheus.HistogramOpts{
			Name:    "gopkg_http_request_duration_seconds",
			Help:    "Duration of HTTP requests handled by gopkg.",
			Buckets: []float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10},
		}, []string{"method", "route"}),
		refsCacheRequests: prometheus.NewCounterVec(prometheus.CounterOpts{
			Name: "gopkg_refs_cache_requests_total",
			Help: "Total number of refs cache lookups by result.",
		}, []string{"result"}),
		refsCacheEntries: prometheus.NewGauge(prometheus.GaugeOpts{
			Name: "gopkg_refs_cache_entries",
			Help: "Number of repository refs entries retained in the in-memory cache.",
		}),
		upstreamRequests: prometheus.NewCounterVec(prometheus.CounterOpts{
			Name: "gopkg_upstream_requests_total",
			Help: "Total number of upstream requests by service, operation, and result.",
		}, []string{"service", "operation", "result"}),
		upstreamRequestDuration: prometheus.NewHistogramVec(prometheus.HistogramOpts{
			Name:    "gopkg_upstream_request_duration_seconds",
			Help:    "Duration of upstream requests by service and operation.",
			Buckets: []float64{0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 300},
		}, []string{"service", "operation"}),
		refsRetries: prometheus.NewCounter(prometheus.CounterOpts{
			Name: "gopkg_refs_retries_total",
			Help: "Total number of GitHub refs request retries after a timeout.",
		}),
		uploadPackBytes: prometheus.NewCounterVec(prometheus.CounterOpts{
			Name: "gopkg_git_upload_pack_bytes_total",
			Help: "Total bytes proxied during git upload-pack requests.",
		}, []string{"direction"}),
	}

	metrics.registry.MustRegister(
		collectors.NewGoCollector(),
		collectors.NewProcessCollector(collectors.ProcessCollectorOpts{}),
		metrics.httpRequests,
		metrics.httpRequestDuration,
		metrics.refsCacheRequests,
		metrics.refsCacheEntries,
		metrics.upstreamRequests,
		metrics.upstreamRequestDuration,
		metrics.refsRetries,
		metrics.uploadPackBytes,
	)
	return metrics
}

func (m *appMetrics) handler() http.Handler {
	return promhttp.HandlerFor(m.registry, promhttp.HandlerOpts{EnableOpenMetrics: true})
}

func (m *appMetrics) observeUpstream(service, operation, result string, started time.Time) {
	m.upstreamRequests.WithLabelValues(service, operation, result).Inc()
	m.upstreamRequestDuration.WithLabelValues(service, operation).Observe(time.Since(started).Seconds())
}

// upstreamResult maps an error from an upstream call to a bounded label value.
func upstreamResult(err error) string {
	switch {
	case err == nil:
		return "ok"
	case errors.Is(err, ErrTimeout), os.IsTimeout(err):
		return "timeout"
	case errors.Is(err, ErrNoRepo):
		return "not_found"
	default:
		return "error"
	}
}

// validateMetricsPath rejects an APP_METRICS_PATH that is relative or that
// would shadow an application route.
func validateMetricsPath(path string) error {
	if !strings.HasPrefix(path, "/") || path == "/" || path == "/health-check" {
		return fmt.Errorf("invalid APP_METRICS_PATH %q: must be an absolute path other than / and /health-check", path)
	}
	return nil
}

// metricsListenAddr returns the address of a dedicated metrics listener, or
// "" when metrics are served on the application port. httpAddr is the -http
// listen address ("[host]:port") and metricsPort the APP_METRICS_PORT value;
// an empty metricsPort or one equal to the application port keeps the single
// listener. A separate port keeps the metrics endpoint off the port that
// ingress publishes.
func metricsListenAddr(httpAddr, metricsPort string) (string, error) {
	if metricsPort == "" {
		return "", nil
	}
	if !validPort(metricsPort) {
		return "", fmt.Errorf("invalid APP_METRICS_PORT %q: must be an integer between 1 and 65535", metricsPort)
	}
	host, port, err := net.SplitHostPort(httpAddr)
	if err != nil {
		return "", fmt.Errorf("invalid listen address %q: %w", httpAddr, err)
	}
	if port == metricsPort {
		return "", nil
	}
	return net.JoinHostPort(host, metricsPort), nil
}

// newHTTPHandler returns the instrumented application handler. When
// metricsPath is not empty, the metrics endpoint is registered on the same
// mux, ahead of the application's catch-all route.
func newHTTPHandler(metricsPath string) http.Handler {
	mux := http.NewServeMux()
	if metricsPath != "" {
		mux.Handle(metricsPath, applicationMetrics.handler())
	}
	mux.Handle("/", observeHTTP(http.HandlerFunc(handler)))
	return mux
}

// newMetricsHandler serves only the metrics endpoint, for the dedicated
// metrics listener; every other path answers 404.
func newMetricsHandler(metricsPath string) http.Handler {
	mux := http.NewServeMux()
	mux.Handle(metricsPath, applicationMetrics.handler())
	return mux
}

type observedResponseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (writer *observedResponseWriter) WriteHeader(statusCode int) {
	if writer.statusCode != 0 {
		return
	}
	writer.statusCode = statusCode
	writer.ResponseWriter.WriteHeader(statusCode)
}

func (writer *observedResponseWriter) Write(body []byte) (int, error) {
	if writer.statusCode == 0 {
		writer.WriteHeader(http.StatusOK)
	}
	return writer.ResponseWriter.Write(body)
}

// Flush keeps streamed responses (git upload-pack) flushing through the wrapper.
func (writer *observedResponseWriter) Flush() {
	if flusher, ok := writer.ResponseWriter.(http.Flusher); ok {
		flusher.Flush()
	}
}

// observeHTTP records a request counter and duration per route and writes
// one structured log record per request. Health checks are counted but not
// logged, because Kubernetes probes them continuously.
func observeHTTP(next http.Handler) http.Handler {
	return http.HandlerFunc(func(resp http.ResponseWriter, req *http.Request) {
		started := time.Now()
		route := requestRoute(req)
		writer := &observedResponseWriter{ResponseWriter: resp}

		next.ServeHTTP(writer, req)
		if writer.statusCode == 0 {
			writer.statusCode = http.StatusOK
		}

		duration := time.Since(started)
		method := requestMethod(req)
		applicationMetrics.httpRequests.WithLabelValues(method, route, strconv.Itoa(writer.statusCode)).Inc()
		applicationMetrics.httpRequestDuration.WithLabelValues(method, route).Observe(duration.Seconds())

		if route != "health_check" {
			logger.Info(
				"request completed",
				"method", req.Method,
				"path", req.URL.Path,
				"route", route,
				"status_code", writer.statusCode,
				"duration_ms", duration.Milliseconds(),
			)
		}
	})
}

// requestMethod maps the request method to one of a fixed set of label
// values. The service answers GET, HEAD and POST; any other token a client
// sends would otherwise create a new time series per distinct value.
func requestMethod(req *http.Request) string {
	switch req.Method {
	case http.MethodGet, http.MethodHead, http.MethodPost:
		return req.Method
	}
	return "other"
}

// requestRoute classifies a request into one of a fixed set of route names,
// mirroring the decisions handler makes, so it can be used as a metric label.
func requestRoute(req *http.Request) string {
	switch req.URL.Path {
	case "/health-check":
		return "health_check"
	case "/":
		return "root_redirect"
	}

	matches := patternNew.FindStringSubmatch(req.URL.Path)
	if matches == nil {
		matches = patternOld.FindStringSubmatch(req.URL.Path)
		if matches == nil {
			return "not_found"
		}
		matches[2], matches[3] = matches[3], matches[2]
	}
	if strings.Contains(matches[3], ".") {
		return "not_found"
	}

	switch matches[4] {
	case "/git-upload-pack":
		return "git_upload_pack"
	case "/info/refs":
		return "git_info_refs"
	}
	if req.URL.Query().Get("go-get") == "1" {
		return "go_get"
	}
	return "package_page"
}

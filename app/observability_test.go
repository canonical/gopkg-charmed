// Copyright 2026 Canonical Ltd.
// See LICENSE file for licensing details.

package main

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/prometheus/client_golang/prometheus/testutil"
)

func withFreshMetrics(t *testing.T) {
	t.Helper()
	original := applicationMetrics
	applicationMetrics = newAppMetrics()
	t.Cleanup(func() { applicationMetrics = original })
}

func serve(handler http.Handler, path string) *httptest.ResponseRecorder {
	recorder := httptest.NewRecorder()
	handler.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, path, nil))
	return recorder
}

func TestMetricsOnApplicationPort(t *testing.T) {
	withFreshMetrics(t)
	handler := newHTTPHandler("/metrics")

	if got := serve(handler, "/health-check"); got.Code != http.StatusOK {
		t.Fatalf("health check status: got %d, want %d", got.Code, http.StatusOK)
	}
	metrics := serve(handler, "/metrics")
	if metrics.Code != http.StatusOK {
		t.Fatalf("metrics status: got %d, want %d", metrics.Code, http.StatusOK)
	}
	for _, metric := range []string{"go_info", "gopkg_http_requests_total"} {
		if !strings.Contains(metrics.Body.String(), metric) {
			t.Errorf("metrics response does not contain %q", metric)
		}
	}
}

func TestMetricsOnDedicatedPort(t *testing.T) {
	withFreshMetrics(t)
	app := newHTTPHandler("")
	metrics := newMetricsHandler("/metrics")

	if got := serve(app, "/metrics"); got.Code != http.StatusNotFound {
		t.Errorf("application handler served /metrics with %d, want %d", got.Code, http.StatusNotFound)
	}
	if got := serve(metrics, "/metrics"); got.Code != http.StatusOK {
		t.Errorf("metrics handler status: got %d, want %d", got.Code, http.StatusOK)
	}
	if got := serve(metrics, "/health-check"); got.Code != http.StatusNotFound {
		t.Errorf("metrics handler served /health-check with %d, want %d", got.Code, http.StatusNotFound)
	}
}

func TestMetricsListenAddr(t *testing.T) {
	tests := []struct {
		httpAddr, metricsPort, want string
		wantErr                     bool
	}{
		{":8080", "", "", false},
		{":8080", "8080", "", false},
		{":8080", "9102", ":9102", false},
		{"127.0.0.1:8080", "9102", "127.0.0.1:9102", false},
		{":8080", "0", "", true},
		{":8080", "metrics", "", true},
		{"8080", "9102", "", true},
	}
	for _, test := range tests {
		got, err := metricsListenAddr(test.httpAddr, test.metricsPort)
		if (err != nil) != test.wantErr {
			t.Errorf("metricsListenAddr(%q, %q) error = %v, wantErr %v", test.httpAddr, test.metricsPort, err, test.wantErr)
			continue
		}
		if got != test.want {
			t.Errorf("metricsListenAddr(%q, %q) = %q, want %q", test.httpAddr, test.metricsPort, got, test.want)
		}
	}
}

func TestValidateMetricsPath(t *testing.T) {
	for _, path := range []string{"metrics", "/", "/health-check", ""} {
		if err := validateMetricsPath(path); err == nil {
			t.Errorf("validateMetricsPath(%q) unexpectedly succeeded", path)
		}
	}
	if err := validateMetricsPath("/metrics"); err != nil {
		t.Errorf("validateMetricsPath(%q) returned an unexpected error: %v", "/metrics", err)
	}
}

func TestRequestRoute(t *testing.T) {
	tests := []struct {
		url  string
		want string
	}{
		{"/health-check", "health_check"},
		{"/", "root_redirect"},
		{"/yaml.v2?go-get=1", "go_get"},
		{"/yaml.v2", "package_page"},
		{"/yaml.v2/info/refs", "git_info_refs"},
		{"/yaml.v2/git-upload-pack", "git_upload_pack"},
		{"/v2/yaml", "package_page"},
		{"/yaml.v2.1", "not_found"},
		{"/unsupported", "not_found"},
	}
	for _, test := range tests {
		t.Run(test.url, func(t *testing.T) {
			req := httptest.NewRequest(http.MethodGet, test.url, nil)
			if got := requestRoute(req); got != test.want {
				t.Errorf("requestRoute(%q): got %q, want %q", test.url, got, test.want)
			}
		})
	}
}

func TestRequestsAreCountedPerRoute(t *testing.T) {
	withFreshMetrics(t)
	handler := newHTTPHandler("/metrics")

	serve(handler, "/health-check")
	serve(handler, "/unsupported")

	if got := testutil.ToFloat64(applicationMetrics.httpRequests.WithLabelValues("GET", "health_check", "200")); got != 1 {
		t.Errorf("health_check counter: got %v, want 1", got)
	}
	if got := testutil.ToFloat64(applicationMetrics.httpRequests.WithLabelValues("GET", "not_found", "404")); got != 1 {
		t.Errorf("not_found counter: got %v, want 1", got)
	}
}

func TestRefsCacheMetrics(t *testing.T) {
	withFreshMetrics(t)
	refsCacheLock.Lock()
	originalCache := refsCache
	refsCache = make(map[string]*refsCacheEntry)
	refsCacheLock.Unlock()
	t.Cleanup(func() {
		refsCacheLock.Lock()
		refsCache = originalCache
		refsCacheLock.Unlock()
	})

	repo := &Repo{Name: "yaml"}
	setRefs(repo.GitHubRoot(), []byte("refs"))
	if _, err := fetchRefs(repo); err != nil {
		t.Fatalf("fetchRefs() returned an unexpected error: %v", err)
	}

	if got := testutil.ToFloat64(applicationMetrics.refsCacheRequests.WithLabelValues("hit")); got != 1 {
		t.Errorf("cache hit counter: got %v, want 1", got)
	}
	if got := testutil.ToFloat64(applicationMetrics.refsCacheEntries); got != 1 {
		t.Errorf("cache entries gauge: got %v, want 1", got)
	}
}

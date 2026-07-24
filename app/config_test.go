package main

import "testing"

func TestEnvOr(t *testing.T) {
	if got := envOr("GOPKG_TEST_UNSET", "fallback"); got != "fallback" {
		t.Errorf("unset var: got %q, want %q", got, "fallback")
	}
	t.Setenv("GOPKG_TEST_SET", "value")
	if got := envOr("GOPKG_TEST_SET", "fallback"); got != "value" {
		t.Errorf("set var: got %q, want %q", got, "value")
	}
	t.Setenv("GOPKG_TEST_EMPTY", "")
	if got := envOr("GOPKG_TEST_EMPTY", "fallback"); got != "fallback" {
		t.Errorf("empty var: got %q, want %q", got, "fallback")
	}
}

func TestDefaultHTTPAddr(t *testing.T) {
	t.Setenv("APP_PORT", "")
	if got := defaultHTTPAddr(); got != ":8080" {
		t.Errorf("no APP_PORT: got %q, want %q", got, ":8080")
	}
	t.Setenv("APP_PORT", "9999")
	if got := defaultHTTPAddr(); got != ":9999" {
		t.Errorf("APP_PORT=9999: got %q, want %q", got, ":9999")
	}
}

func TestValidPort(t *testing.T) {
	valid := []string{"1", "80", "8080", "65535"}
	for _, p := range valid {
		if !validPort(p) {
			t.Errorf("validPort(%q) = false, want true", p)
		}
	}
	invalid := []string{"", "0", "-1", "65536", "8080x", "localhost:8080", "http", " 80"}
	for _, p := range invalid {
		if validPort(p) {
			t.Errorf("validPort(%q) = true, want false", p)
		}
	}
}

func TestValidateHostname(t *testing.T) {
	valid := []string{"gopkg.in", "localhost", "staging.example.com", "localhost:8080", "a-b.c-d.io", "x", "9lives.io"}
	for _, h := range valid {
		if err := validateHostname(h); err != nil {
			t.Errorf("validateHostname(%q) = %v, want nil", h, err)
		}
	}
	invalid := []string{
		"",                  // empty
		"https://staging.x", // scheme
		"gopkg.in/",         // trailing slash
		"gopkg.in/pkg",      // path
		"host name.io",      // space
		"-lead.io",          // label starts with hyphen
		"trail-.io",         // label ends with hyphen
		"dot..dot.io",       // empty label
		"gopkg.in:",         // colon without port
		"gopkg.in:0",        // port out of range
		"gopkg.in:65536",    // port out of range
		"gopkg.in:git",      // non-numeric port
		"user@gopkg.in",     // userinfo
	}
	for _, h := range invalid {
		if err := validateHostname(h); err == nil {
			t.Errorf("validateHostname(%q) = nil, want error", h)
		}
	}
}

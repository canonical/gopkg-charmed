// Copyright 2026 Canonical Ltd.
// See LICENSE file for licensing details.

// Package main is a placeholder web server that keeps the rock and charm
// pipeline buildable until the real Go application is imported into this
// repository. Replace this file (and go.mod) with the imported application.
package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
)

func main() {
	port := os.Getenv("APP_PORT")
	if port == "" {
		port = "8080"
	}
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintln(w, "Hello from gopkg")
	})
	log.Printf("listening on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}

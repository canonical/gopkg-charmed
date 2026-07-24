# gopkg.in — Stable APIs for the Go language

See [http://gopkg.in](http://gopkg.in).

## About this repository

This repository hosts the source of the gopkg.in service, imported as a
snapshot from [niemeyer/gopkg](https://github.com/niemeyer/gopkg), and is
the operated source of truth for the service going forward.

## Repository layout

The service is scoped to the [app/](app/) folder, which is the permanent Go
project root and the home of the entire 12-factor pipeline: the Go source and
`go.mod` live there today, and the rock (`app/rockcraft.yaml`) and charm
(`app/charm/`) — built with the 12-factor `go-framework` extensions for
Rockcraft and Charmcraft — will be added there as the re-platforming
progresses. A pre-built 12-factor scaffold is available on the
`charm-scaffold` branch for reference.

The repository root is deliberately reserved for sibling concerns that need
separation from the app: `docs/` (release-notes tooling, existing), and in
the future `terraform/` (deployment module) and `tests/` (integration
tests).

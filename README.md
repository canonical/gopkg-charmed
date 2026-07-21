# gopkg.in — Stable APIs for the Go language

See [http://gopkg.in](http://gopkg.in).

## About this repository

This repository hosts the source of the gopkg.in service, imported as a
snapshot from [niemeyer/gopkg](https://github.com/niemeyer/gopkg), and is
the operated source of truth for the service going forward. The service
source currently lives in [app/](app/) while the repository is being set
up; it will move to the repository root as part of the 12-factor layout.

The rock and charm (built with the 12-factor `go-framework` extensions for
Rockcraft and Charmcraft) and the Terraform deployment module will be added
as the re-platforming progresses. A pre-built 12-factor scaffold is
available on the `charm-scaffold` branch for reference.

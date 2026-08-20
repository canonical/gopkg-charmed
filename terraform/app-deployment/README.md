# gopkg app deployment module

Deploys the gopkg charm into an existing Juju model in a cloud-agnostic way.

## Scope

This module manages:

- gopkg charm deployment
- gopkg charm config (`hostname`)
- gopkg OCI resource (`app-image`)
- optional nginx ingress deployment and integration
- optional trust/constraints

This module does not create Juju controllers or models.

## Example usage

```hcl
module "gopkg_app" {
  source = "../../terraform/app-deployment"

  model_uuid          = var.model_uuid
  gopkg_app_name      = "gopkg"
  gopkg_charm_name    = "gopkg"
  gopkg_charm_channel = "latest/edge"
  gopkg_hostname      = "gopkg.example.com"
  gopkg_app_image     = "ghcr.io/canonical/gopkg@sha256:replace-me"

  deploy_ingress           = true
  ingress_service_hostname = "gopkg.example.com"
  ingress_path_routes      = "/"
  ingress_rewrite_enabled  = false
}
```

## Notes

- Keep `ingress_rewrite_enabled = false` for gopkg, matching repository deployment guidance.
- Prefer pinning both charm revision and OCI image digest for repeatable environments.
- For cloud-specific provisioning (controller/model/bootstrap), compose this module from higher-level stacks.

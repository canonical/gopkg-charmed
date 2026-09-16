# Contributing

This document explains the processes and practices recommended for
contributing enhancements to the gopkg-k8s project.

## Overview

- Generally, before developing enhancements to this charm, you should
  consider [opening an issue](https://github.com/canonical/gopkg-charmed/issues)
  explaining your use case.
- If you would like to chat with us about your use cases or proposed
  implementation, you can reach us at the
  [Canonical Matrix public channel](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
  or on [Discourse](https://discourse.charmhub.io/).
- Familiarizing yourself with the
  [Juju documentation](https://canonical.com/juju/docs/juju-cli/3.6/howto/manage-charms/)
  will help you a lot when working on new features or bug fixes.
- All enhancements require review before being merged. Code review typically
  examines
  - code quality
  - test coverage
  - user experience for Juju operators of this charm.
- Once your pull request is approved, we squash and merge your pull request
  branch onto the `main` branch. This creates a linear Git commit history.
- For further information on contributing, please refer to our
  [Contributing Guide](https://github.com/canonical/platform-engineering-contributing-guide).
- The engineering standards this repository follows are collected in
  [repo-compliance.md](repo-compliance.md).

## Code of conduct

When contributing, you must abide by the
[Ubuntu Code of Conduct](https://ubuntu.com/community/docs/ethos/code-of-conduct).

## Security

To report a vulnerability, follow the process in [SECURITY.md](SECURITY.md).
Do not open a public issue for security problems.

## Release notes

This project does not keep a changelog file. Every user-relevant change ships
with a release-note artifact instead:

- Copy
  [`docs/release-notes/template/_change-artifact-template.yaml`](docs/release-notes/template/_change-artifact-template.yaml)
  to `docs/release-notes/artifacts/pr<NNNN>.yaml`, where `<NNNN>` is your pull
  request number padded to four digits (`pr0027.yaml` for PR #27), and fill it
  in.
- If your change is not user-relevant, add the `no-release-note` label to the
  pull request instead.

The "Check for release notes artifact" workflow enforces this on every pull
request.

To publish the release notes for a release:

1. Copy
   [`docs/release-notes/template/_release-artifact-template.yaml`](docs/release-notes/template/_release-artifact-template.yaml)
   to `docs/release-notes/releases/release<NNNN>.yaml`, where `<NNNN>` is the
   next release number, and fill it in, listing the change artifacts the
   release includes.
2. Merge it to `main`. The "Create release notes" workflow renders
   `docs/release-notes/release-notes-<NNNN>.md` from
   `docs/release-notes/template/release-template.md.j2` and opens a pull
   request with the page.
3. In that pull request, complete the requirements table and the known
   issues, and add the page to the "Releases" list and the toctree in
   `docs/release-notes/index.rst`.

The rendered pages are published in the
[documentation](docs/release-notes/index.rst).

## Submissions

If you want to address an issue or a bug in this project, notify in advance
the people involved to avoid confusion; also, reference the issue or bug
number when you submit the changes.

- [Fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-forks)
  our [GitHub repository](https://github.com/canonical/gopkg-charmed) and add
  the changes to your fork, properly structuring your commits, providing
  detailed commit messages and signing your commits.
- Make sure the updated project builds and runs without warnings or errors;
  this includes linting, documentation, code and tests.
- Submit the changes as a
  [pull request (PR)](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork).

Your changes will be reviewed in due time; if approved, they will be
eventually merged.

### AI

You are free to use any tools you want while preparing your contribution,
including AI, provided that you do so lawfully and ethically.

Avoid using AI to complete issues tagged with the "good first issues" label.
The purpose of these issues is to provide newcomers with opportunities to
contribute to our projects and gain coding skills. Using AI to complete these
tasks undermines their purpose.

We have created instructions and tools that you can provide AI while
preparing your contribution:
[`copilot-collections`](https://github.com/canonical/copilot-collections)

While it isn't necessary to use `copilot-collections` while preparing your
contribution, these files contain details about our quality standards and
practices that will help the AI avoid common pitfalls when interacting with
our projects. By using these tools, you can avoid longer review times and
nitpicks.

If you choose to use AI, please disclose this information to us by indicating
AI usage in the PR description (for instance, marking the checklist item about
AI usage). You don't need to go into explicit details about how and where you
used AI.

Avoid submitting contributions that you don't fully understand. You are
responsible for the entire contribution, including the AI-assisted portions.
You must be willing to engage in discussion and respond to any questions,
comments, or suggestions we may have.

### Signing commits

To improve contribution tracking, we use the
[Canonical contributor license agreement](https://assets.ubuntu.com/v1/ff2478d1-Canonical-HA-CLA-ANY-I_v1.2.pdf)
(CLA) as a legal sign-off, and we require all commits to have verified
signatures.

#### Canonical contributor agreement

Canonical welcomes contributions to the gopkg-k8s project. Please check
out our [contributor agreement](https://canonical.com/legal/contributors) if
you're interested in contributing to the solution.

The CLA sign-off is a simple line at the end of the commit message certifying
that you wrote it or have the right to commit it as an open-source
contribution.

#### Verified signatures on commits

All commits in a pull request must have cryptographic (verified) signatures.
To add signatures on your commits, follow the
[GitHub documentation](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits).

## Develop

The documentation contains detailed, CI-tested contribution guides. Start
there rather than duplicating the steps here:

- [Improve the documentation](docs/contribute/improve-documentation.rst):
  build, preview, and check the documentation on Linux or macOS.
- [Improve the code](docs/contribute/improve-code.rst): run the Go, charm, and
  Juju integration tests for changes to the service, the charm, or the rock.

Both guides start from the prepared Ubuntu environment described in the
documentation. In short, every code contribution runs:

```bash
cd app
test -z "$(gofmt -l .)" && go vet ./... && go build ./... && go test -race ./...
cd charm
tox -e lint,unit,static
cd ../..
app/charm/tests/integration/run_full_local_suite.sh
```

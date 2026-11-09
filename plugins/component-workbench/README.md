# component-workbench 0.1.1

**Experimental; not catalog-approved, production-certified, or security-audited.**

Propose immutable file maps, validate syntax, freeze evaluation specs, and record review attestations.

## Tools and hooks

Tools: `workbench_propose`, `workbench_validate`, `workbench_freeze`, `workbench_review`, `workbench_status`, `workbench_diff`.
Hooks: none.

## Installation

Use a reviewed Git repository URL, its full commit SHA and subdirectory `plugins/component-workbench`:
`hermes -p YOUR_PROFILE plugins install "REPOSITORY_URL#plugins/component-workbench" --ref FULL_COMMIT_SHA --yes-deps --no-enable`.
Replace both placeholders; no public repository is claimed yet. Inspect the source and scanner output, then:
`hermes -p YOUR_PROFILE plugins enable component-workbench --no-allow-tool-override`.
Start a new session. Never disable security scans to force an install.

## Example use

Use workbench_propose, workbench_validate and workbench_freeze; submit results using workbench_review, then inspect workbench_status.


## Data, privacy and effects

Storage: local SQLite candidate/review database, under Hermes's profile-scoped `plugin_data_dir('component-workbench')` when applicable.
No plugin-originated network requests, shell commands, background processes, training, or self-updates.
The routing plugin returns a route to Hermes; Hermes may subsequently call that configured provider.
Native plugins run with host authority; these boundaries are contracts, not OS sandboxing.
No credential stores are read. Do not put secrets in captured passages or artifact text.

## Limits

Does not execute submitted code, authenticate verifier identity, install/promote candidates, or prove evaluation provenance. Review attestations are caller-supplied.

## Compatibility and tests

Hermes floor: `>=0.23.0`. Tested on the installed Windows Hermes v0.23.0 environment with Python 3.14.9;
the floor is not a promise that every future version/platform has been tested.
Dependencies: jsonschema>=4.0,<5 plus Python standard library and Hermes public APIs.
Use Hermes's managed environment; do not independently upgrade its pinned core dependencies.
From this repository root:

```bash
python -m unittest test_06_workbench -v
hermes plugins doctor plugins/component-workbench --ci
hermes plugins validate plugins/component-workbench --json
```

## Disable, remove, and data retention

`hermes -p YOUR_PROFILE plugins disable component-workbench`; start a new session to guarantee unloading.
`hermes -p YOUR_PROFILE plugins remove component-workbench` removes code through the normal CLI.
Do not assume this deletes data: preserve/export or deliberately delete the plugin's own data directory separately.
No automatic data deletion is implemented by this plugin. MIT license; see LICENSE.

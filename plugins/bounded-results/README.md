# bounded-results 0.1.1

**Experimental; not catalog-approved, production-certified, or security-audited.**

Bound allowlisted large research-tool results and retrieve their full content by hash.

## Tools and hooks

Tools: `bounded_read`.
Hooks: `transform_tool_result`.

## Installation

Use a reviewed Git repository URL, its full commit SHA and subdirectory `plugins/bounded-results`:
`hermes -p YOUR_PROFILE plugins install "REPOSITORY_URL#plugins/bounded-results" --ref FULL_COMMIT_SHA --yes-deps --no-enable`.
Replace both placeholders; no public repository is claimed yet. Inspect the source and scanner output, then:
`hermes -p YOUR_PROFILE plugins enable bounded-results --no-allow-tool-override`.
Start a new session. Never disable security scans to force an install.

## Example use

Invoke an allowlisted evidence/evaluation tool with a large result; inspect the returned content handle, then use bounded_read for complete chunks.


## Data, privacy and effects

Storage: local content-addressed result files, under Hermes's profile-scoped `plugin_data_dir('bounded-results')` when applicable.
No plugin-originated network requests, shell commands, background processes, training, or self-updates.
The routing plugin returns a route to Hermes; Hermes may subsequently call that configured provider.
Native plugins run with host authority; these boundaries are contracts, not OS sandboxing.
No credential stores are read. Do not put secrets in captured passages or artifact text.

## Limits

4096-byte preview policy; stored inputs are limited to 8 MB, and oversize inputs pass through. This is neither a secret redactor nor a universal size/security guard. Full stored content may be sensitive.

## Compatibility and tests

Hermes floor: `>=0.23.0`. Tested on the installed Windows Hermes v0.23.0 environment with Python 3.14.9;
the floor is not a promise that every future version/platform has been tested.
Dependencies: jsonschema>=4.0,<5 plus Python standard library and Hermes public APIs.
Use Hermes's managed environment; do not independently upgrade its pinned core dependencies.
From this repository root:

```bash
python -m unittest test_03_bounded -v
hermes plugins doctor plugins/bounded-results --ci
hermes plugins validate plugins/bounded-results --json
```

## Disable, remove, and data retention

`hermes -p YOUR_PROFILE plugins disable bounded-results`; start a new session to guarantee unloading.
`hermes -p YOUR_PROFILE plugins remove bounded-results` removes code through the normal CLI.
Do not assume this deletes data: preserve/export or deliberately delete the plugin's own data directory separately.
No automatic data deletion is implemented by this plugin. MIT license; see LICENSE.

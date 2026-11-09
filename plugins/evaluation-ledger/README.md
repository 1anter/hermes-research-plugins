# evaluation-ledger 0.2.0

**Experimental; not catalog-approved, production-certified, or security-audited.**

Store immutable artifacts and optionally collect allowlisted usage/event fields.

## Tools and hooks

Tools: `evaluation_artifact`, `evaluation_check`, `evaluation_report`.
Hooks: `post_api_request`, `api_request_error`, `post_tool_call`.

## Installation

Use a reviewed Git repository URL, its full commit SHA and subdirectory `plugins/evaluation-ledger`:
`hermes -p YOUR_PROFILE plugins install "REPOSITORY_URL#plugins/evaluation-ledger" --ref FULL_COMMIT_SHA --yes-deps --no-enable`.
Replace both placeholders; no public repository is claimed yet. Inspect the source and scanner output, then:
`hermes -p YOUR_PROFILE plugins enable evaluation-ledger --no-allow-tool-override`.
Start a new session. Never disable security scans to force an install.

## Example use

Save text with evaluation_artifact; compare its hash and optional JSON with evaluation_check. Use evaluation_report with explicit session_ids.

## Collection consent

Collection defaults OFF, even when the plugin is enabled. Explicit artifact tools remain available.
Opt in for a chosen profile with:

```bash
hermes -p YOUR_PROFILE config set plugins.entries.evaluation-ledger.settings.observe_usage true
```
Set the same key to `false` to opt out, and start a new session. Consent is snapshotted at registration.
Automatic collection stores allowlisted identifiers, route/model names, status and nonnegative usage counters only.
It does not store prompts, responses, tool arguments/results, error text, URLs or credentials and never exports telemetry.
Explicit artifact capture stores exactly the content you supply; do not supply secrets.

## Data, privacy and effects

Storage: ledger.sqlite, under Hermes's profile-scoped `plugin_data_dir('evaluation-ledger')` when applicable.
No plugin-originated network requests, shell commands, background processes, training, or self-updates.
The routing plugin returns a route to Hermes; Hermes may subsequently call that configured provider.
Native plugins run with host authority; these boundaries are contracts, not OS sandboxing.
No credential stores are read. Do not put secrets in captured passages or artifact text.

## Limits

Observers are best-effort, not complete billing. Include child session IDs explicitly. Report cache/reasoning fields separately; do not double-count. Artifact text is user-supplied and may itself be sensitive.

## Compatibility and tests

Hermes floor: `>=0.23.0`. Tested on the installed Windows Hermes v0.23.0 environment with Python 3.14.9;
the floor is not a promise that every future version/platform has been tested.
Dependencies: jsonschema>=4.0,<5 plus Python standard library and Hermes public APIs.
Use Hermes's managed environment; do not independently upgrade its pinned core dependencies.
From this repository root:

```bash
python -m unittest test_02_ledger test_09_ledger_consent -v
hermes plugins doctor plugins/evaluation-ledger --ci
hermes plugins validate plugins/evaluation-ledger --json
```

## Disable, remove, and data retention

`hermes -p YOUR_PROFILE plugins disable evaluation-ledger`; start a new session to guarantee unloading.
`hermes -p YOUR_PROFILE plugins remove evaluation-ledger` removes code through the normal CLI.
Do not assume this deletes data: preserve/export or deliberately delete the plugin's own data directory separately.
No automatic data deletion is implemented by this plugin. MIT license; see LICENSE.

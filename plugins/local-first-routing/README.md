# local-first-routing 0.2.0

**Experimental; not catalog-approved, production-certified, or security-audited.**

Select an explicitly approved delegation provider/model, with no automatic fallback.

## Tools and hooks

Tools: `local_route_policy`.
Hooks: none.

## Installation

Use a reviewed Git repository URL, its full commit SHA and subdirectory `plugins/local-first-routing`:
`hermes -p YOUR_PROFILE plugins install "REPOSITORY_URL#plugins/local-first-routing" --ref FULL_COMMIT_SHA --yes-deps --no-enable`.
Replace both placeholders; no public repository is claimed yet. Inspect the source and scanner output, then:
`hermes -p YOUR_PROFILE plugins enable local-first-routing --no-allow-tool-override`.
Start a new session. Never disable security scans to force an install.

## Example use

Use local_route_policy to inspect the defaults and settings location. Configure the approved route explicitly before selecting delegation.backend=local-first.

## Approved routing pins

Defaults retain provider `custom` and model `DeepSeek-V4.1-Flash-1017` for compatibility.
Set `delegation.backends.local-first.approved_provider` and `delegation.backends.local-first.approved_model`
using `hermes config set`; the ordinary `delegation.provider` and `delegation.model` must match those pins exactly.
Nonblank strings are required. Task text cannot override the pins. No fallback provider is returned.
After configuring an actually local endpoint through Hermes, select `delegation.backend=local-first` explicitly.
Installing this plugin alone does not alter your existing delegation backend or provider credentials.
Safety refusal, auth/quota/outage/timeout, already-verified, and manual-review states remain distinct.

## Data, privacy and effects

Storage: none, under Hermes's profile-scoped `plugin_data_dir('local-first-routing')` when applicable.
No plugin-originated network requests, shell commands, background processes, training, or self-updates.
The routing plugin returns a route to Hermes; Hermes may subsequently call that configured provider.
Native plugins run with host authority; these boundaries are contracts, not OS sandboxing.
No credential stores are read. Do not put secrets in captured passages or artifact text.

## Limits

Caller-declared outcomes are not authenticated. The plugin does not enforce timeouts or guarantee that a user-configured endpoint is physically local. It does not automatically activate the backend or implement a 30/70 token quota.

## Compatibility and tests

Hermes floor: `>=0.23.0`. Tested on the installed Windows Hermes v0.23.0 environment with Python 3.14.9;
the floor is not a promise that every future version/platform has been tested.
Dependencies: jsonschema>=4.0,<5 plus Python standard library and Hermes public APIs.
Use Hermes's managed environment; do not independently upgrade its pinned core dependencies.
From this repository root:

```bash
python -m unittest test_05_routing test_08_routing_settings -v
hermes plugins doctor plugins/local-first-routing --ci
hermes plugins validate plugins/local-first-routing --json
```

## Disable, remove, and data retention

`hermes -p YOUR_PROFILE plugins disable local-first-routing`; start a new session to guarantee unloading.
`hermes -p YOUR_PROFILE plugins remove local-first-routing` removes code through the normal CLI.
Do not assume this deletes data: preserve/export or deliberately delete the plugin's own data directory separately.
No automatic data deletion is implemented by this plugin. MIT license; see LICENSE.

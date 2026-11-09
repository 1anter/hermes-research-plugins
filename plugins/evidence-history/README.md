# evidence-history 0.2.1

**Experimental; not catalog-approved, production-certified, or security-audited.**

Capture supplied passages, preserve revisions and choose evidence by publication and actual observation time.

## Tools and hooks

Tools: `evidence_capture`, `evidence_as_of`, `evidence_history`, `evidence_compare`, `evidence_verify_support`.
Hooks: none.

## Installation

Use a reviewed Git repository URL, its full commit SHA and subdirectory `plugins/evidence-history`:
`hermes -p YOUR_PROFILE plugins install "REPOSITORY_URL#plugins/evidence-history" --ref FULL_COMMIT_SHA --yes-deps --no-enable`.
Replace both placeholders; no public repository is claimed yet. Inspect the source and scanner output, then:
`hermes -p YOUR_PROFILE plugins enable evidence-history --no-allow-tool-override`.
Start a new session. Never disable security scans to force an install.

## Example use

Ask Hermes to capture a supplied source passage with its publication timestamp, then use evidence_as_of with mode known_to_system. Use published_by only for explicitly retrospective questions.


## Data, privacy and effects

Storage: evidence.sqlite, under Hermes's profile-scoped `plugin_data_dir('evidence-history')` when applicable.
No plugin-originated network requests, shell commands, background processes, training, or self-updates.
The routing plugin returns a route to Hermes; Hermes may subsequently call that configured provider.
Native plugins run with host authority; these boundaries are contracts, not OS sandboxing.
No credential stores are read. Do not put secrets in captured passages or artifact text.

## Limits

Capture does not fetch/authenticate a URL. Exact quote/value checks do not prove semantic entailment. Publication metadata is supplied by the caller. Storage is append-only through this API, not tamper-proof.

## Compatibility and tests

Hermes floor: `>=0.23.0`. Tested on the installed Windows Hermes v0.23.0 environment with Python 3.14.9;
the floor is not a promise that every future version/platform has been tested.
Dependencies: Python standard library and Hermes public APIs.
Use Hermes's managed environment; do not independently upgrade its pinned core dependencies.
From this repository root:

```bash
python -m unittest test_01_evidence -v
hermes plugins doctor plugins/evidence-history --ci
hermes plugins validate plugins/evidence-history --json
```

## Disable, remove, and data retention

`hermes -p YOUR_PROFILE plugins disable evidence-history`; start a new session to guarantee unloading.
`hermes -p YOUR_PROFILE plugins remove evidence-history` removes code through the normal CLI.
Do not assume this deletes data: preserve/export or deliberately delete the plugin's own data directory separately.
No automatic data deletion is implemented by this plugin. MIT license; see LICENSE.

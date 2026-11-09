# Hermes research plugins — experimental release

Five native plugins with individual READMEs, MIT licenses, dependency/compatibility metadata and reproducible tests.
Temporal-memory is deliberately excluded: its private ContextCompressor dependency remains unresolved.

## Reproduce

Use the Hermes-managed Python environment with jsonschema and PyYAML; run `python run_checks.py`.
This runs development tests and native Doctor/catalog validation, not inference or live activation.
Optional: `python run_checks.py --skip-native` for source-only unit tests.
Individual test commands are in each plugin README. Current results are generated under checks/.
These are development and parent-reviewed tests, not independent certification.

## Lifecycle and use

Install a reviewed Git commit using its `#plugins/NAME` subdirectory and full SHA, initially disabled.
No public repository or catalog listing is claimed until a real remote URL and review exist.
Only evidence-history and evaluation-ledger are intended for the initial selective profile rollout.
Ledger observer collection is explicitly opt-in and local only; see its README.
The routing backend and your context engine are NOT automatically selected.

## Scope of evidence

Prior synthetic experiments supported the evidence-selection mechanism, not plugin packaging alone.
Do not infer that all five plugins improve quality, speed or token use, or that Astra usage is capped at 30%.
The configurable-routing change was authored by a local worker; its test defects required one parent repair batch.
No untouched-independent verification or public maintainer approval is claimed.

## Public-release gate

Read every plugin README and SECURITY.md; run acceptance at the exact frozen commit; choose the public owner/repository;
publish only source, docs and tests, never local databases, credentials, logs or experiment transcripts.
Prepare catalog YAML with the real HTTPS repository, full commit SHA, subdir and matching capabilities.
Submit a maintainer-reviewed PR to NousResearch/hermes-agent. Catalog acceptance is not automatic.

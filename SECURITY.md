# Security and disclosure

Experimental native Python plugins execute with the host user's authority, not in an OS sandbox.
No external telemetry, credential-file reads, self-updaters, shell commands or background services are implemented.
Persistent data can contain sensitive user-supplied source passages, candidate code and artifacts.
The ledger observes a narrow field allowlist only after explicit opt-in; usage coverage is best-effort.
The bounded-results plugin stores full allowlisted results and is not a redactor. Oversize inputs can pass through.
The route selector trusts administrator configuration and caller-declared outcome labels; it is not an authenticated security boundary.
Review IDs and evaluator reports are not authenticated by component-workbench.
Do not use these experimental plugins as a sole basis for financial, legal or safety-critical decisions.
Report suspected flaws to the eventual repository maintainer without including secrets or private captured data.
There is no automatic promotion, update or dependency refresh. Revalidate all upgrades before deployment.

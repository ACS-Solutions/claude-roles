---
name: standards
description: Generic standards for cross-cutting concerns — logging, telemetry (traces, metrics, health), error handling, configuration and resilience — and how a repository's own house rules in .claude/standards/xcut.md override them. Use when writing or changing code that logs, catches or throws exceptions, reads configuration, makes outbound calls, or adds tracing or metrics, and whenever reviewing such code.
---

# Cross-cutting concerns standards

These are defaults. **A repository's house rules win.** Before applying anything here, read, in order:

1. `.claude/standards/xcut.md` in the repository root, if present: the house rules for cross-cutting concerns.
2. `CLAUDE.md` (root and any nearer the code in question) for anything it says about these concerns.

Where a house rule contradicts a rule below, follow the house rule and do not report the generic one. Where the house rules say a concern is deliberately absent (for example "no metrics: logs are the only telemetry"), do not recommend adding it.

For language and framework specifics, also load the matching skill:

- .NET (Serilog, Microsoft.Extensions.Logging, OpenTelemetry, ASP.NET Core): `xcut:dotnet`

## Rule IDs

Findings cite these IDs, or the house rule's own ID (`H-…`) where one applies.

### LOG — Logging

- **LOG1 Structured.** Messages are templates with named properties (`"Order {OrderId} shipped"`), never strings built by interpolation or concatenation. Property names are consistent across the codebase: the same thing has the same name everywhere.
- **LOG2 Levels mean something.** Use the house level policy. Default: Debug for diagnostics only a developer wants; Information for lifecycle and significant business events; Warning for something unexpected that was handled; Error for a failed operation that needs attention; Critical/Fatal for the process or a whole subsystem failing.
- **LOG3 Context.** Every log written within a unit of work (request, message, connection, job) carries the identifiers needed to group it: correlation/trace id, plus the entity ids the house rules name. Prefer scopes or enrichers over repeating them by hand, unless the house rules prescribe a message prefix.
- **LOG4 No secrets or personal data.** Credentials, tokens, connection strings, keys and personal data never reach a log, including through exception messages, request/response dumps or configuration dumps. Use the house redaction helpers wherever they exist.
- **LOG5 Exceptions logged once, where handled.** The code that handles an exception logs it, with its type and inner exceptions in the house-prescribed form. No log-and-rethrow at every layer; no logging an exception and then also returning it to a caller that logs it again.
- **LOG6 Proportionate volume.** No Information-or-above logs inside per-item or per-packet loops. Expensive arguments are not computed when the level is disabled.
- **LOG7 Actionable.** A Warning or Error says what was being attempted, on what, what happened, and what the system did next (retried, dropped, stopped).
- **LOG8 Lifecycle.** Startup logs name, version and a redacted configuration summary; shutdown is logged; state transitions of long-lived components (connected, disconnected, degraded) are logged.
- **LOG9 Output target detected reliably.** Choosing a log format or sink from the environment (journald, a terminal, a container) uses the signal the platform documents, not one that child processes inherit. For example, `JOURNAL_STREAM` alone does not mean stdout is the journal: systemd says to compare its `device:inode` with stdout's or stderr's.

### TEL — Telemetry beyond logs

Apply only where the house rules adopt tracing or metrics; otherwise at most one standards observation.

- **TEL1 Traces.** Inbound requests, outbound calls, queue sends/receives and significant internal operations produce spans; context propagates across async, queue and process boundaries.
- **TEL2 Metrics.** Key operations record rate, errors and duration. Tag cardinality is bounded: no user ids, URLs with ids, or exception messages as tag values.
- **TEL3 Health.** Long-running services expose liveness/readiness, or the house equivalent, and readiness reflects dependencies the service cannot work without.
- **TEL4 One identity.** Service name, version and environment are set once and appear on all logs, traces and metrics.

### ERR — Error handling

- **ERR1 Nothing silently swallowed.** An empty or log-free `catch` is allowed only for best-effort cleanup or an expected condition, and says why in a comment.
- **ERR2 Catch narrowly.** Catch specific exception types. Broad catches belong only at boundaries (top level, request pipeline, message handler, background loop) and must log.
- **ERR3 Cancellation is not an error.** Cancellation and shutdown-time disposal exceptions are not logged as errors, but a cancellation that was *not* requested is not hidden either.
- **ERR4 Consistent error contract.** Errors leave the process in one house-defined shape: exit codes, HTTP problem details, error codes or typed results. New failure categories extend that contract rather than inventing a new one.
- **ERR5 Background work is observed.** Fire-and-forget tasks, timers and event handlers catch and log their own exceptions; nothing can fault unobserved or crash the process from a background thread.

### CFG — Configuration

- **CFG1 Fail fast.** Configuration is bound to typed settings and validated at startup, before side effects; error messages name the setting key and the offending value (unless it is sensitive).
- **CFG2 No committed secrets.** Committed configuration files hold no secrets; secrets come from the environment, a credential store or a vault.
- **CFG3 Documented defaults.** Every setting has a sensible default or is required, and required settings fail CFG1 when missing.

### RES — Resilience and resources

- **RES1 Timeouts.** Every outbound call (HTTP, database, relay, queue) has a bounded timeout or a cancellation token tied to one.
- **RES2 Retries with judgement.** Retries are for transient failures, use backoff with jitter, are bounded, and only repeat idempotent operations.
- **RES3 Disposal.** Connections, streams, sockets and other disposables are disposed on every path, including failure and cancellation.
- **RES4 Graceful shutdown.** Stop signals stop intake, drain in-flight work within a bounded time, and flush logs and telemetry before exit.

## Out of scope

Leave these to other roles or reviews: security vulnerabilities beyond secret leakage (security role), functional correctness (code review), formatting and naming style, test coverage, performance beyond logging volume.

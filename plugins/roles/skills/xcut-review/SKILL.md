---
name: xcut-review
description: Run the cross-cutting concerns reviewer (logging, telemetry, error handling, configuration, resilience) on the current diff, given paths, the whole repository, or in survey mode to draft house rules.
argument-hint: "[diff | path <paths…> | all | survey]"
disable-model-invocation: true
---

Launch the `roles:xcut-reviewer` subagent with this request, passing the mode and scope through unchanged:

> Mode and scope: $ARGUMENTS
> (empty means: review the diff of the current branch against its base, including uncommitted changes)

Relay its report to the user as it stands. Do not fix anything unless the user then asks you to.

If the mode was `survey` and the user wants the draft kept, write it to `.claude/standards/xcut.md` in the repository root.

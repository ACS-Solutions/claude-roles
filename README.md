# claude-roles

Specialist roles for Claude Code, shared across all my repositories. Each role is a generic expert; each repository supplies its own house rules, which the role reads before it works.

This repository is a Claude Code [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) containing one plugin, `roles`.

## Roles

| Role | Kind | What it does |
|---|---|---|
| `xcut-reviewer` | gatekeeper / auditor | Logging, telemetry, error handling, configuration and resilience, checked against the repo's house rules. Read-only. |

## How a role is built

```
plugins/roles/
  agents/<role>.md               the role: system prompt, tool limits, preloaded skills
  skills/<role>-standards/       the expertise: generic rules with IDs
  skills/<role>-dotnet/          language specifics for those rules, one skill per language
  skills/<role>-review/          the /roles:<role>-review command that dispatches the agent
```

The expertise lives in skills, not in the agent, so the main session can load it while *writing* code as well as having the agent use it when *reviewing*. Language specifics are separate skills preloaded by the agent, not reference files inside a skill: a subagent running headless may not be allowed to read files from the plugin directory, but preloaded skills arrive in its context regardless.

## House rules in each repository

Each repository using a role keeps its conventions in `.claude/standards/<concern>.md`, for example `.claude/standards/xcut.md`. House rules override the generic rules. They should say what the repository does, cite example files, and state deliberate absences ("no tracing: logs are the only telemetry") so the role does not recommend them.

To bootstrap one, run `/roles:xcut-review survey` in the repository, then edit the draft and commit it.

## Using it

**Trying out a local checkout** (no install):

```sh
claude --plugin-dir ~/dev/gh/alasdaircs/claude-roles/plugins/roles
```

**Installing for yourself** on any machine:

```
/plugin marketplace add alasdaircs/claude-roles
/plugin install roles@claude-roles
```

**Enabling it for a repository** (so that cloud sessions and anyone cloning the repo get it), in the repo's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "claude-roles": { "source": { "source": "github", "repo": "alasdaircs/claude-roles" } }
  },
  "enabledPlugins": { "roles@claude-roles": true }
}
```

Then:

```
/roles:xcut-review                 # diff of this branch against its base
/roles:xcut-review path src/Foo    # specific files or folders
/roles:xcut-review all             # whole repository
/roles:xcut-review survey          # draft .claude/standards/xcut.md
```

The main session can also delegate to the `roles:xcut-reviewer` agent on its own initiative, for example before opening a PR.

## Adding a role

1. Write `skills/<role>-standards/SKILL.md`: rules with stable IDs, concrete and checkable, with an "Out of scope" section that names the neighbouring roles.
2. Write `agents/<role>.md`: limit its tools, preload the standards skill, define its report format and severities.
3. Add a `/roles:<role>-review` command skill if it will be invoked by hand.
4. Bump `version` in `plugins/roles/.claude-plugin/plugin.json`.
5. Pilot it on one repository before relying on it.

## References

- [Plugins](https://code.claude.com/docs/en/plugins) and the [plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [Subagents](https://code.claude.com/docs/en/sub-agents)
- [Skills](https://code.claude.com/docs/en/skills)

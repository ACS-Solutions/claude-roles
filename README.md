# claude-roles

Specialist roles for Claude Code, shared across all my repositories. Each role is a generic expert; each repository supplies its own house rules, which the role reads before it works.

This repository is a Claude Code [plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) with one plugin per role, so each repository enables only the roles it wants.

## Roles

| Plugin | Agent | Kind | What it does |
|---|---|---|---|
| `xcut` | `xcut:reviewer` | gatekeeper / auditor | Logging, telemetry, error handling, configuration and resilience, checked against the repo's house rules. Read-only. |

## How a role is built

Each role is a self-contained plugin; the plugin name is the role's namespace, so its parts have plain names:

```
plugins/<role>/
  .claude-plugin/plugin.json     name, version, description
  agents/reviewer.md             the agent (<role>:reviewer): system prompt, tool limits, preloaded skills
  skills/standards/              the expertise (<role>:standards): generic rules with IDs
  skills/dotnet/                 language specifics for those rules (<role>:dotnet), one skill per language
  skills/review/                 the /<role>:review command that dispatches the agent
```

A role that is not a reviewer names its agent after what it does (`auditor`, `advisor`).

The expertise lives in skills, not in the agent, so the main session can load it while *writing* code as well as having the agent use it when *reviewing*. Language specifics are separate skills preloaded by the agent, not reference files inside a skill: a subagent running headless may not be allowed to read files from the plugin directory, but preloaded skills arrive in its context regardless.

## House rules in each repository

Each repository using a role keeps its conventions in `.claude/standards/<role>.md`, for example `.claude/standards/xcut.md`. House rules override the generic rules. They should say what the repository does, cite example files, and state deliberate absences ("no tracing: logs are the only telemetry") so the role does not recommend them.

To bootstrap one, run `/xcut:review survey` in the repository, then edit the draft and commit it.

## Using it

**Trying out a local checkout** (no install):

```sh
claude --plugin-dir ~/dev/gh/alasdaircs/claude-roles/plugins/xcut
```

**Installing for yourself** on any machine:

```
/plugin marketplace add alasdaircs/claude-roles
/plugin install xcut@claude-roles
```

**Enabling roles for a repository** (so that cloud sessions and anyone cloning the repo get them), in the repo's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "claude-roles": { "source": { "source": "github", "repo": "alasdaircs/claude-roles" } }
  },
  "enabledPlugins": { "xcut@claude-roles": true }
}
```

Then:

```
/xcut:review                 # diff of this branch against its base
/xcut:review path src/Foo    # specific files or folders
/xcut:review all             # whole repository
/xcut:review survey          # draft .claude/standards/xcut.md
```

The main session can also delegate to the `xcut:reviewer` agent on its own initiative, for example before opening a PR.

## Adding a role

1. Create `plugins/<role>/.claude-plugin/plugin.json` with `name: "<role>"` and `version: "0.1.0"`, and add an entry for it to `.claude-plugin/marketplace.json`.
2. Write `skills/standards/SKILL.md`: rules with stable IDs, concrete and checkable, with an "Out of scope" section that names the neighbouring roles. Add a skill per language for language specifics.
3. Write `agents/<agent>.md`: limit its tools, preload the standards and language skills, define its report format and severities.
4. Add a `skills/review/SKILL.md` command if it will be invoked by hand.
5. Keep the plugin self-contained: nothing outside `plugins/<role>/` is installed with it.
6. Bump `version` in the role's `plugin.json` on every change, and run `claude plugin validate` on the marketplace and the plugin.
7. Pilot it on one repository before relying on it.

## References

- [Plugins](https://code.claude.com/docs/en/plugins) and the [plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [Subagents](https://code.claude.com/docs/en/sub-agents)
- [Skills](https://code.claude.com/docs/en/skills)

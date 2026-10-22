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

**Register the marketplace once per machine**, with auto-update on:

```sh
claude plugin marketplace add alasdaircs/claude-roles
```

Then set `"autoUpdate": true` on its entry under `extraKnownMarketplaces` in `~/.claude/settings.json`, or use `/plugin` → **Marketplaces** → **Enable auto-update**. Auto-update is off by default for any marketplace that isn't Anthropic's.

**Enable a role in a repository**, in the repo's committed `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "claude-roles": { "source": { "source": "github", "repo": "alasdaircs/claude-roles" }, "autoUpdate": true }
  },
  "enabledPlugins": { "xcut@claude-roles": true }
}
```

It loads once the folder's workspace trust dialog has been accepted in an interactive session; `claude -p` doesn't count, so headless runs need the user-scope install below or `--plugin-dir`. No per-machine install is needed: a plugin with a relative-path source loads from the marketplace itself. The `extraKnownMarketplaces` entry registers the marketplace on machines that don't have it yet.

**Enable a role in every repository on a machine**: `claude plugin install xcut@claude-roles` (user scope).

**Cloud sessions** ignore the plugins and marketplaces a repository declares in `.claude/settings.json`, and they don't see your user settings either. Install the role from the cloud environment's setup script instead:

```sh
export CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1
claude plugin marketplace add alasdaircs/claude-roles
claude plugin install xcut@claude-roles
```

The environment caches what the setup script installed for up to about seven days. Edit the script to force a rebuild sooner, or run `claude plugin update xcut@claude-roles` then `/reload-plugins` inside a session.

Then:

```
/xcut:review                 # diff of this branch against its base
/xcut:review path src/Foo    # specific files or folders
/xcut:review all             # whole repository
/xcut:review survey          # draft .claude/standards/xcut.md
```

The main session can also delegate to the `xcut:reviewer` agent on its own initiative, for example before opening a PR.

## Developing and releasing

There are two ways to run a role, and they should not be mixed up:

- **Development**: `claude --plugin-dir ~/dev/gh/alasdaircs/claude-roles/plugins/xcut` loads the working tree as it stands, uncommitted edits included, and overrides an installed copy of the same plugin. Use it only in the session editing the role, and in at most one pilot session that knowingly runs unreleased rules.
- **Installed**: every other session gets the role from the marketplace on GitHub, so it only ever sees what has been released.

To release a change:

1. Bump `version` in the role's `plugin.json`. Installed copies are cached by version, so a push without a bump reaches no one.
2. Run `claude plugin validate .` and `claude plugin validate plugins/<role>`.
3. Commit and push to `main`.

Machines with auto-update on refresh the marketplace in the background, within ten minutes of the first message in a session, and load the new version at their next session start (or at `/reload-plugins`). Elsewhere, run `claude plugin marketplace update claude-roles`, or `claude plugin update <role>@claude-roles` for a plugin installed at user scope. To see which version a machine has, run `claude plugin list`.

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

## Licence

[MIT](LICENSE).

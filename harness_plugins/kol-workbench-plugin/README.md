# KOL Workbench DeepSeek Harness Plugin

This bundle exposes the local KOL Workbench runtime as DeepSeek Harness tools.

## Extracted Harness Concepts

- A Harness plugin is a module exporting `name` and `apply(ctx)`.
- Tool plugins declare `inject = ['tools']` so Cordis waits for the tool registry.
- Tools are registered through `ctx.tools.register(defineTool(...))`.
- `parameters` describe model-callable arguments and are validated by Harness.
- `execute(args)` returns the canonical value.
- `output.render` converts the value into model-facing content.
- Installable bundles declare `dsh.bundle.patch` in `package.json`.
- Bundle patch files reference the package by package name, then `dsh plugin add` installs the layer into a profile.

## Tools

- `kol_workbench_status`: read summary, model config metadata, and Gmail account placeholders.
- `kol_list_leads`: list local KOL leads with filters.
- `kol_create_manual_lead`: create one manual KOL lead.
- `kol_generate_gmail_drafts`: generate local Gmail outreach drafts.
- `kol_list_gmail_drafts`: list local draft records.
- `kol_open_gmail_compose`: open a configured browser/Profile with Gmail compose prefilled.
- `kol_record_gmail_sent`: record a draft as sent after human Gmail sending.

## Safety Boundary

The plugin talks only to the local KOL Workbench Agent API.

It does not:

- read Gmail passwords, cookies, OAuth tokens, or browser login state;
- send Gmail automatically;
- upload draft bodies, prompts, sessions, or secrets to Supabase.

`kol_open_gmail_compose` only opens a browser compose URL. The user must review and send in Gmail manually, then call `kol_record_gmail_sent`.

## Install Into Harness

From the directory that contains this repository:

```sh
dsh plugin --profile kol-bd add ./WorkBench/harness_plugins/kol-workbench-plugin
dsh --profile kol-bd --dump-config
dsh --profile kol-bd
```

If running Harness from source, use `pnpm dsh` from the DeepSeek Harness checkout and pass the path to this plugin directory.

## Configure Runtime URL

The bundle defaults to:

```txt
http://127.0.0.1:8766
```

Change it in `cordis.patch.yml`:

```yaml
- insert:
    - id: kol-workbench-tools
      name: dsh-kol-workbench-plugin
      config:
        baseUrl: http://127.0.0.1:8766
```

Or set:

```sh
set KOL_WORKBENCH_URL=http://127.0.0.1:8766
```

Start the local workbench before using tools:

```sh
D:\yloy\Documents\WorkBench\start_kol_workbench.bat
```

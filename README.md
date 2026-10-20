# SolidWorks MCP

**Control SolidWorks with the AI assistant you already use.**

Connect Claude Desktop, Cursor, or Codex to SolidWorks and automate supported modeling, inspection, and engineering tasks using natural language. The server runs on the same Windows PC as SolidWorks. You confirm a change before it touches the model.

**[Install SolidWorks MCP](INSTALLATION.md)** · **[See Daksh CWM](https://dakshcwm.com/)**

SolidWorks MCP is a local MCP server. Your assistant starts one process, named `solidworks`, and talks to the open session in plain language. Companion skills tell that assistant which supported call to make.

This repository publishes the installer, release notes, and companion skills. The server source stays with [Cad Workflow Manager](https://dakshcwm.com/). See [LICENSE](LICENSE).

## What you can ask it to do

Ask in the units you already use. The companion skill converts lengths and angles for the tools that need meters and radians.

**Model.** Create and edit the open part: sketches, extrudes, holes, patterns, shells, dimensions, relations, fillets, and sheet metal. Rebuild and save when the step is done.

**Inspect.** Read the model before you trust it: mass properties, feature errors, What’s Wrong, interference, section views, a captured view, assembly structure, and the BOM.

**Finish the engineering step.** Export a drawing to PDF or DXF, write STEP from a save, and set units and custom properties. Look up a SolidWorks API member and its signature before the assistant calls it.

The `solidworks-bridge-tool-selection` skill records which calls work through this server. A call that needs a macro waits until you agree. Sample prompts are in [EXAMPLES.md](EXAMPLES.md).

## How a request runs

1. You ask Claude Desktop, Cursor, Codex, or Claude Code in ordinary language.
2. The assistant calls the local server. One process keeps one session.
3. A write shows a Yes/No dialog titled SolidWorks MCP. **No** leaves the model unchanged.
4. The assistant reads that result, then continues. After a major feature it can capture the view and quote the feature names and mass from the tool result.

Reads such as API lookup can run with SolidWorks closed. Modeling and inspection use the SolidWorks session on that PC.

## Clients

| Client | How it connects |
|---|---|
| Claude Desktop | The setup writes the `solidworks` server into Claude Desktop’s config. |
| Cursor | The setup writes it into `%USERPROFILE%\.cursor\mcp.json`. |
| Codex | The setup writes it into `%USERPROFILE%\.codex\config.toml`. |
| Claude Code | Add the same installed exe yourself. The command is in [INSTALLATION.md](INSTALLATION.md). |

ChatGPT Work calls remote MCP. Use Codex on the PC where SolidWorks is open. Client questions are in [FAQ.md](FAQ.md).

## Install

Download `CWMSolidWorksMCPSetup.exe` from the Releases page for this repository, and compare the published SHA-256 before you run it. Until the first release is attached, use a build supplied by Cad Workflow Manager.

The setup installs for the current user, under `%USERPROFILE%\CWM\SolidWorksMcp`. By default it registers Claude Desktop, Cursor, and Codex, and copies the companion skills into skill folders that already exist.

You need Windows x64 and SolidWorks on that PC. The setup includes the runtime the host needs.

Full steps, quiet-install switches, and how to remove the registration are in [INSTALLATION.md](INSTALLATION.md).

## Try a prompt

The server name in the client is `solidworks`.

> Extrude the selected sketch 12 mm and tell me the mass.

> What is wrong with the open part?

> Walk this assembly, extract the BOM, and check for interference.

> Export the active drawing to PDF.

> Look up the SolidWorks API member for this call and show the signature first.

With the default write policy, the extrude, the save, and the export each wait for your Yes. `read-only` refuses writes. `trusted` skips the dialog. A part-modeling-only tool list is described in [EXAMPLES.md](EXAMPLES.md).

## Companion skills

Skills live in [skills/](skills/README.md). They teach the assistant how to drive the open model, look up the API, size a part, build an assembly, and turn a finished conversation into a procedure. The server itself ships in the installer.

The installer copies every published skill into Cursor, Codex, Claude Code, and an existing Claude Desktop Cowork space. Edit skills in the SolidWorks MCP product. The product copies them into this repository.

## Your files stay on this PC

The host runs on your PC, with no account and no telemetry of its own. Tool traffic stays between the assistant and the local process. Configuration is the `appsettings.json` beside the installed exe. What the server reads, what it writes, and what it leaves to SolidWorks is in [PRIVACY.md](PRIVACY.md).

## When the job has to run the same way every time

SolidWorks MCP is the conversation with the model that is open.

[Daksh CWM](https://dakshcwm.com/) is the workflow product from the same team, for the release work a team repeats: PDF, DXF, and STEP exports, file names, folders, and approvals, on the SolidWorks files you already have. Engineers lay out those steps in a visual builder and run them with a desktop agent.

Use SolidWorks MCP for the model that is open. Use Daksh CWM when those release steps need to run the same way for the whole team.

**[See Daksh CWM](https://dakshcwm.com/)** · **[Workflow features](https://dakshcwm.com/features/)** · **[Plans](https://dakshcwm.com/pricing/)** · [sales@cloudcadai.com](mailto:sales@cloudcadai.com)

## In this repository

- [INSTALLATION.md](INSTALLATION.md) — setup, registration, requirements
- [EXAMPLES.md](EXAMPLES.md) — prompts, units, write policy, tool profile
- [FAQ.md](FAQ.md) — source, clients, privacy, versions
- [skills/](skills/README.md) — companion skills
- [PRIVACY.md](PRIVACY.md) — what stays on the PC
- [CHANGELOG.md](CHANGELOG.md) — what each public release contains
- [SECURITY.md](SECURITY.md) — how to report a vulnerability

GitHub’s MCP Registry is a discovery page. The registry package is an `.mcpb` file on a GitHub Release. `server.example.json` shows the shape of that metadata. Publish it only after the real `.mcpb` asset and its SHA-256 exist.

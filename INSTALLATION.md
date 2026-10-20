# Installation

SolidWorks MCP is a Windows desktop program. The download is `CWMSolidWorksMCPSetup.exe` on the GitHub Releases page for this repository. Each release also publishes the SHA-256 of that file. Compare it before you run the setup.

The setup is per-user. It does not ask for an administrator. Files install under:

`%USERPROFILE%\CWM\SolidWorksMcp`

That folder holds `CWM.SolidWorks.Mcp.Host.exe`, `appsettings.json`, and the companion skills. The setup does not create a Start menu shortcut. A later release upgrades the previous per-user install in place.

## What the setup turns on

These options are selected by default:

| Option | What it does |
|---|---|
| SolidWorks MCP Server | Installs the host. Required. |
| Register with Claude Desktop | Writes the `solidworks` server into Claude Desktop's config. |
| Register with Cursor | Writes the `solidworks` server into `%USERPROFILE%\.cursor\mcp.json`. |
| Register with Codex | Writes the `solidworks` server into `%USERPROFILE%\.codex\config.toml`. |
| Install companion skill | Copies every published skill into skill folders that already exist. |

Quiet install keeps those options on:

```text
CWMSolidWorksMCPSetup.exe /quiet
```

Turn one off with `RegisterClaude=0`, `RegisterCursor=0`, `RegisterCodex=0`, or `InstallSkill=0`.

## After install

Reload MCP servers in Cursor, or restart Cursor. Restart Claude Desktop. The server name is `solidworks`.

The registered command is:

`C:\Users\<user>\CWM\SolidWorksMcp\CWM.SolidWorks.Mcp.Host.exe`

Claude Code does not read the Claude Desktop config. Add the same exe yourself:

```text
claude mcp add solidworks -- "C:\Users\<user>\CWM\SolidWorksMcp\CWM.SolidWorks.Mcp.Host.exe"
```

You can register or copy skills again from the installed host:

```text
CWM.SolidWorks.Mcp.Host.exe --register
CWM.SolidWorks.Mcp.Host.exe --install-skill
```

`--install-skill` leaves a missing `.cursor`, `.codex`, or `.claude` folder alone. Open Claude Desktop once, while signed in, before installing skills there, then restart Desktop.

## Requirements

- Windows x64
- SolidWorks, for tools that change or read the open model
- No separate .NET install. The setup contains the runtime the host needs

`search_api` can look up the reflected SolidWorks API without a running SolidWorks process. Modeling tools need SolidWorks.

## Remove

Uninstall SolidWorks MCP from Windows settings. When a registration option was installed, uninstall removes that client entry.

# FAQ

## Where is the source?

This is a public distribution repository. The C# implementation is not published here. Releases contain the installer. The `skills/` folder contains the companion skills copied from the product.

## Which clients can connect?

Claude Desktop, Claude Code, Cursor, and Codex on the same PC. Each one starts the local exe and talks to it on standard input and output.

ChatGPT Work cannot use this host. It calls remote MCP and does not read the local Codex config or the local skill folders. Use Codex on the same PC.

## Does the setup need administrator rights?

No. Install and upgrade are per-user, under `%USERPROFILE%\CWM\SolidWorksMcp`.

## What gets sent off this computer?

The host does not add an account or its own telemetry. Tool traffic stays between the client and the local process. See [PRIVACY.md](PRIVACY.md).

## How do new skills show up here?

Skills are added in the SolidWorks MCP product as `skill/<name>/SKILL.md`. The product copies every such folder into `skills/` in this repository, and the installer copies those same folders onto a computer. A skill that exists only in this repository is replaced the next time that copy runs.

## Why are there two release files?

`CWMSolidWorksMCPSetup.exe` is the Windows setup. It installs the host, can register Claude Desktop, Cursor, and Codex, and can copy the skills.

`solidworks.mcpb` is the package the MCP registry can install. The registry listing does not replace this repository or the setup. Publish the registry metadata only after that `.mcpb` file and its SHA-256 exist on a GitHub Release.

## Which version is this?

The host version packaged today is `0.0.6`. The changelog in this repository tracks what each public release contains.

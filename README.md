# SolidWorks MCP

Local MCP server for SolidWorks. Claude Desktop, Claude Code, Cursor, and Codex start one Windows process and talk to it on standard input and output. The server name is `solidworks`.

This is a public distribution repository for Cad Workflow Manager. It publishes the installer, release notes, and companion skills. It is not an open-source repository: the server source is not included. See [LICENSE](LICENSE).

## Download

GitHub Releases for this repository will attach:

| File | Purpose |
|---|---|
| `CWMSolidWorksMCPSetup.exe` | Per-user Windows setup |
| `CWMSolidWorksMCPSetup.exe.sha256` | SHA-256 of that setup |
| `solidworks.mcpb` | Registry package, when a registry listing is published |
| Release notes | What changed in that version |

Until the first release is attached, use a build supplied by Cad Workflow Manager. Install steps are in [INSTALLATION.md](INSTALLATION.md).

## In this repository

- [INSTALLATION.md](INSTALLATION.md)
- [EXAMPLES.md](EXAMPLES.md)
- [FAQ.md](FAQ.md)
- [skills/](skills/README.md)
- [PRIVACY.md](PRIVACY.md)
- [CHANGELOG.md](CHANGELOG.md)
- [SECURITY.md](SECURITY.md)

## Skills

Companion skills live in [skills/](skills/README.md). They tell the client how to call the server. They do not contain the server.

New skills are added in the SolidWorks MCP product. That product copies every `skill/<name>/SKILL.md` folder into this repository. Edit the skills there, then update this repository from that copy.

## Registry

GitHub's MCP Registry is a discovery page. Listing there is separate from this repository and from the product site.

The registry package is an `.mcpb` file on a GitHub Release, with its SHA-256 recorded in `server.json`. `server.example.json` shows the shape of that file. Fill in the release URL and the real hash when the first `.mcpb` asset exists, then publish. Do not publish the example hash.

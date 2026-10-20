# Privacy

SolidWorks MCP runs on your computer. Cursor, Claude Desktop, Claude Code, or Codex starts `CWM.SolidWorks.Mcp.Host.exe` and talks to it through standard input and output. One process keeps one local session.

The server reads and writes the SolidWorks session on that same computer. With the default write policy, a write tool asks you to confirm it in a dialog before it runs.

Configuration is a local `appsettings.json` beside the installed exe, under `%USERPROFILE%\CWM\SolidWorksMcp`. Client registration edits the local MCP config for the clients you select. Skill install copies the skill files into skill folders that already exist on that computer.

This server does not add an account, a license check, or its own telemetry. SolidWorks itself is a separate product and follows its own network behavior.

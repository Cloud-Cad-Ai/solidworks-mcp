# Privacy

SolidWorks MCP runs on your computer. Cursor, Claude Desktop, Claude Code, or Codex starts `CWM.SolidWorks.Mcp.Host.exe` and talks to it through standard input and output. One process keeps one local session.

The server reads and writes the SolidWorks session on that same computer. With the default write policy, a write tool asks you to confirm it in a dialog before it runs.

Configuration is a local `appsettings.json` beside the installed exe, under `%USERPROFILE%\CWM\SolidWorksMcp`. Client registration edits the local MCP config for the clients you select. Skill install copies the skill files into skill folders that already exist on that computer.

Startup contacts the license service at `https://www.cloudcadai.com/wp-json/cwm-mcp/v1`. The request sends the Windows machine id. That id is the same for every Windows account on the PC, and deleting `license.dat` does not change it. One trial is available for that machine, and it starts without a card. The length is set on the license service. When the trial ends, the host asks you to subscribe and the card is entered on Stripe’s page. `license.dat` in `%USERPROFILE%\CWM\SolidWorksMcp` remembers the last successful check and, for a trial, when that trial ends. If the service cannot be reached, a paid subscription stays available for 72 hours after the last success. A trial stays available only until that trial end, and only inside those 72 hours.

The host also posts usage totals to that address: host version, Windows version, SolidWorks version when the installed interop reports it, write policy, tool profile, MCP client name and version, tool name, outcome (`ok`, `error`, `denied`, `blocked`), duration, exception type name, and for `invoke` and `describe_api` the SolidWorks API member name. It does not send prompts, tool arguments, file paths, document or feature names, mass properties, BOM rows, custom properties, screenshots from `capture_view`, exception message text, or `search_api` queries.

SolidWorks itself is a separate product and follows its own network behavior.

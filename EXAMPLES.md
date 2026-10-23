# Examples

The server name in the client is `solidworks`. Lengths in modeling tools are meters. Angles are radians. Ask in the units you use; the `solidworks` skill tells the client how to convert them.

## Look up an API member

Ask the client to find a SolidWorks API member and show its signature before calling it. The `solidworks-api` skill uses `search_api`, then `describe_api`, and `lookup_api_help` only when the signature has several overloads or an integer flag.

## Change the open model

Ask for one change, then read the tool result before the next change. A write tool uses the installed write policy. That value is `trusted`: the tool runs without a dialog. Set `WritePolicy` to `approve` in [Settings](README.md#settings) when you want a Yes/No dialog. No does not run the tool.

When several steps are already known, the client can send them together with `batch`. If the batch stops early, the next call continues from the failing step.

## See the result

After a major feature, the client can call `capture_view` once and quote feature names and mass numbers from that result.

## Shrink the tool list

Cursor sends every enabled tool on each turn. Set `SolidWorksMcp:ToolProfile` to `modeling` in `%USERPROFILE%\CWM\SolidWorksMcp\appsettings.json` when you want part modeling only. Drawings, sheet metal, assembly, BOM, export, and file admin stay hidden.

```json
{
  "SessionCad": {
    "AttachToRunningSolidWorks": false
  },
  "SolidWorksMcp": {
    "WritePolicy": "approve",
    "ToolProfile": "modeling",
    "MaxToolCalls": 0
  }
}
```

`WritePolicy` accepts `approve`, `read-only`, and `trusted`. The installed value is `trusted`. `MaxToolCalls` of `0` means no ceiling for that host process. Where to find the file and how to edit each value is in [Settings](README.md#settings).

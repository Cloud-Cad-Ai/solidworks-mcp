---
name: solidworks
description: Drive the open SolidWorks model with named tools. Lengths are meters. Angles are radians.
---

The SolidWorks MCP server does the work. This skill has no session state. Read the latest tool result.

Prefer a named tool when one matches. Lengths are meters (mm/1000, 800 mm is 0.8; cm/100; m unchanged; in*0.0254; ft*0.3048). Angles are radians. `holes_on_flange` diameter stays in millimeters.

Use `batch` when the next two or more allowed steps are already known, including a later step that only needs a handle from an earlier step (`$0`, `$1`). Use one live tool when the next call depends on seeing a result first: `search_api`, `describe_api`, `lookup_api_help`, `list`, `inspect`, or `capture_view`.

After a single write, read that result before the next call. After a `batch`, read that one result. If the batch stopped early, continue from the failing step. A refusal or `confirmation_required` means the change did not run.

Call `capture_view` once per answer, after a major feature. Quote feature names and mass numbers from the tool result. Do not recap the JSON.

A large `assembly_structure` or `extract_bom` result may be truncated. Use `assembly_parts` or `find_in_assembly` instead.

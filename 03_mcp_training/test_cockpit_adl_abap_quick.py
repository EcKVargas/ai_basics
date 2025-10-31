#!/usr/bin/env python3
"""Quick test for cockpit_get_view_by_sid('ADL', systype='ABAPSystem')
Saves full JSON to cockpit_ADL_ABAP_test.json and prints a short summary.
"""
import json
import traceback
from server import cockpit_get_view_by_sid

SID = "ADL"
SYSTYPE = "ABAPSystem"
OUTFILE = "cockpit_ADL_ABAP_test.json"

print(f"Calling cockpit_get_view_by_sid('{SID}', systype='{SYSTYPE}')")
try:
    result = cockpit_get_view_by_sid(SID, systype=SYSTYPE)
except Exception:
    print("Exception while calling cockpit_get_view_by_sid:")
    traceback.print_exc()
    raise

if isinstance(result, dict) and result.get("error"):
    print("Function returned error:", result.get("error"))
else:
    print("Function succeeded. Showing short summary:")
    resolved = result.get("_resolved") if isinstance(result, dict) else None
    if resolved:
        print("  Resolved object id:", resolved.get("objectid"))
        print("  SID:", resolved.get("sid"))
        print("  systemtype:", resolved.get("systemtype"))
    # program_landscape clients count
    clients = result.get("program_landscape", {}).get("clients") if isinstance(result, dict) else None
    if isinstance(clients, list):
        print("  Clients count:", len(clients))

# save full result
try:
    with open(OUTFILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Saved full response to {OUTFILE}")
except Exception as e:
    print("Failed to save result:", e)

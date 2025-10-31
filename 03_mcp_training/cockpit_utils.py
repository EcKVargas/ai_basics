# cockpit_utils.py
import requests
import json

FLEXI_BASE = "https://dlm.wdf.sap.corp/slim"
COCKPIT_BASE = "https://dlm.wdf.sap.corp/slim/API/UI5CockpitDataProvider"


def _resolve_objectid_from_sid(sid: str, systype: str | None = None) -> dict:
    """
    Resolve a Cockpit objectid based on SID via Flexi Report.
    Ignores entries with status 'Canceled'.
    """
    fields = ["id", "sid", "systemtype", "landscape", "status"]
    # Only query Flexi by SID; system type is not required by the Flexi API and
    # historically caused empty results. If a systype is provided, we'll filter
    # returned entries client-side.
    filters = [f"sid|{sid}"]

    url = f"{FLEXI_BASE}/report/flexi"

    # Helper to call Flexi with a constructed query string and return parsed entries
    def call_flexi(query_string: str):
        params = {"sw": "f", "otype": "json", "query": query_string}
        resp = requests.get(url, params=params, timeout=20, verify=False)
        resp.raise_for_status()
        try:
            data = resp.json()
        except ValueError:
            text = resp.text
            preview = text[:1000] + ("..." if len(text) > 1000 else "")
            raise RuntimeError(f"Flexi API returned non-JSON response. Preview: {preview}")

        # If API returned a list directly
        if isinstance(data, list):
            return data
        # If API returned a JSON string, try to parse
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                return []

        # Normal dict case: try known nested locations
        entries = data.get("data", {}).get("variable", {}).get("Entries") or data.get("data", {}).get("Entries") or data.get("Entries")
        if isinstance(entries, list):
            return entries
        return []

    # Build query candidates to try (start with the more detailed, then simpler)
    candidate_queries = [
        ",".join(fields + filters),
        f"id,sid|{sid}",
        f"sid|{sid}",
    ]

    entries = []
    for q in candidate_queries:
        try:
            entries = call_flexi(q)
        except Exception:
            entries = []
        if entries:
            break

    # If a systype filter was provided, filter returned entries client-side
    if systype and entries:
        filtered = []
        for e in entries:
            st = (e.get("systemtype") or e.get("SystemType") or "")
            if st and st.lower() == systype.lower():
                filtered.append(e)
        if filtered:
            entries = filtered

    if not entries:
        raise RuntimeError(f"No system found for SID '{sid}'.")

    # Normalize casing
    norm = []
    for e in entries:
        norm.append({
            "id": e.get("id") or e.get("ID") or e.get("SISMKey"),
            "sid": e.get("sid") or e.get("SID"),
            "systemtype": e.get("systemtype") or e.get("SystemType"),
            "landscape": e.get("landscape") or e.get("Landscape"),
            "status": (e.get("status") or e.get("Status") or "").strip()
        })

    # Filter out canceled
    active = [e for e in norm if e["status"].lower() not in ("canceled", "cancelled")]

    if not active:
        raise RuntimeError(f"All systems for SID '{sid}' are canceled.")

    best = active[0]
    return {
        "objectid": str(best["id"]),
        "sid": best["sid"],
        "systemtype": best["systemtype"],
        "landscape": best["landscape"],
        "status": best["status"]
    }


def _fetch_cockpit(objectid: str, systype: str = "ABAPSystem") -> dict:
    """Fetch the full Cockpit JSON for a given objectid."""
    params = {"systype": systype, "objectid": objectid}
    resp = requests.get(COCKPIT_BASE, params=params, timeout=30, verify=False)
    resp.raise_for_status()
    # Try to return JSON; if the endpoint returns plain text or unexpected payload,
    # raise a clear error so callers can handle it.
    try:
        data = resp.json()
        print("Cockpit API returned JSON data",data)
    except ValueError:
        # Not JSON — include a truncated preview to help debugging
        text = resp.text
        preview = text[:1000] + ("..." if len(text) > 1000 else "")
        raise RuntimeError(
            f"Cockpit API returned non-JSON response for objectid={objectid}, systype={systype}. "
            f"Preview: {preview}"
        )

    if not isinstance(data, dict):
        # Defensive: some endpoints might return a string or list; raise informative error
        raise RuntimeError(
            f"Unexpected JSON type from Cockpit API: {type(data).__name__} (expected object/dict) for objectid={objectid}"
        )

    return data


def _normalize_cockpit(raw: dict, sections: list[str] | None = None) -> dict:
    """Normalize Cockpit JSON into a compact, structured response."""
    sections = set(sections or ["system_details", "availability", "program_landscape" , "Clients", "Software_Components"])
    out = {}

    if "system_details" in sections:
        mi = raw.get("Main System Info") or {}
        out["system_details"] = {
            "sid": raw.get("SID"),
            "description": raw.get("Description"),
            "status": raw.get("Availability Tooltip") ,
            "flp_connections": raw.get("FLPConnections"),
            "lpd_connections": raw.get("LPDConnections"),
            "r3logon_link": raw.get("R3Logon Link"),
            "type": mi.get("System Type"),
            "product_version": mi.get("Product Version"),
            "DB_host": mi.get("DB_host"),
            "HDB_Instance": mi.get("HDB Instance"),
            "DB_Type": mi.get("DB Type"),
            "HANA_Version": mi.get("HANA Version"),
            "HANA Release": mi.get("HANA Release"),
            "SISM Link": mi.get("HANA Release"),
            "Basis_Release": mi.get("Basis Release"),
            "app_server": mi.get("AppServer"),
            "created_on": mi.get("CreatedOn")
        }

    if "main_info" in sections:
       
        out["main_info"] = {
        
        }

    if "availability" in sections:
        # mi = raw.get("Main System Info") or {}
        out["availability"] = {
            "sysmon_notes": raw.get("Sysmon Notes"),
            "snow_landscape_down_tickets": raw.get("SNOW Landscape Down Tickets", 0),
            "open_snow_tickets": raw.get("Open SNOW Tickets", 0)
        }

    if "program_landscape" in sections:
        responsibles = []
        ap = raw.get("Assigned Programs") or {}
        mi = raw.get("Main System Info") or {}
        if mi.get("ProgramLead"):
            responsibles.append({"role": "Prog Lead", "name": ap["Prog Lead"]})
        if raw.get("PLO"):
            responsibles.append({"role": "PLO", "name": mi["PLO"]})

        out["program_landscape"] = {
            "landscape_name": raw.get("LandscapeName") or raw.get("Landscape"),
            "responsibles": responsibles,
            "upcoming_milestone": raw.get("Upcoming Milestones")
        }

    if "Clients" in sections:
         out["Clients"] = {
            "clients": raw.get("Clients"),
        }
         
    if "Software_Components" in sections:
        out["Software_Components"] = {
        "Software Components": raw.get("Software Components"),
    }     
    return out

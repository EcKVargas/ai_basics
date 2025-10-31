# Test version without tools to isolate asyncio issue
import os, json
from typing import List
from mcp.server.fastmcp import FastMCP
import requests
import httpx
from urllib.parse import quote_plus
from typing import List, Dict, Any
from cockpit_utils import _resolve_objectid_from_sid, _fetch_cockpit, _normalize_cockpit
import logging
import time
import traceback

# configure simple logging for traceability (adjust level as needed)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


mcp = FastMCP( 
    name="Test MCP Server",
    host="0.0.0.0",
    port=8050,
)

@mcp.tool()
def greet(name: str) -> str:
    return f"Hello, {name}!"

@mcp.tool()
def search_system_flexi(fields: list[str], filters: list[str] = None,
                         otype: str = "json",
                         base_url: str = "https://dlm.wdf.sap.corp/slim"):
    query = ",".join(fields + (filters or []))
    url = f"{base_url}/report/flexi"
    params = {
        "sw": "f",
        "otype": otype,
        "query": query
    }
    print("Calling Flexi:", url, "params=", params)
    resp = requests.get(url, params=params, timeout=20, verify=False)

    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(
            f"HTTP error calling Flexi API: {e}, status={resp.status_code}, text={resp.text}"
        ) from e

    # Return parsed JSON entries if JSON was requested; otherwise raw text (XML/CSV)
    if otype.lower() == "json":
        data = resp.json()
        # Prefer the typical structure data -> Entries, but fall back if different
        try:
            return data["data"]["Entries"]
        except (KeyError, TypeError):
            return data
    else:
        return resp.text
    
@mcp.tool()
def cockpit_get_view_by_sid(sid: str, systype: str | None = None, sections: list[str] | None = None):
    """
    Resolve SID -> objectid, fetch cockpit, normalize and return view.
    Improved traceability: logs each step, returns traceback on error and
    optionally saves raw payload when DEBUG_COCKPIT_SAVE env var is set.
    """
    logger = logging.getLogger("mcp.tool.cockpit_get_view_by_sid")
    start = time.time()
    ctx = {"sid": sid, "systype": systype, "sections": sections}
    logger.info("starting cockpit_get_view_by_sid %s", ctx)

    # 1) resolve
    try:
        res = _resolve_objectid_from_sid(sid=sid, systype=systype)
        logger.info("resolved SID -> objectid: %s", res.get("objectid"))
    except Exception as e:
        tb = traceback.format_exc()
        logger.exception("resolve_objectid failed: %s", e)
        return {"error": f"Failed to resolve object id from SID '{sid}': {e}", "step": "resolve", "trace": tb}

    objectid = res.get("objectid")
    if not objectid:
        msg = f"Resolver returned no objectid for SID '{sid}'"
        logger.error(msg + " resolver_result=%s", res)
        return {"error": msg, "step": "resolve", "resolver_result": res}

    # 2) fetch cockpit
    try:
        raw = _fetch_cockpit(objectid=objectid, systype=systype or "ABAPSystem")
        if isinstance(raw, dict):
            logger.info("fetched cockpit payload (dict) keys=%s", list(raw.keys()))
        else:
            logger.info("fetched cockpit payload type=%s len=%d", type(raw).__name__, len(str(raw)))
    except Exception as e:
        tb = traceback.format_exc()
        logger.exception("fetch_cockpit failed: %s", e)
        return {"error": f"Failed to fetch cockpit for objectid {objectid}: {e}", "step": "fetch", "trace": tb}

    # optional: persist raw payload for debugging if env var set
    if os.environ.get("DEBUG_COCKPIT_SAVE"):
        try:
            debug_fn = f"cockpit_debug_{sid}_{objectid}.json"
            with open(debug_fn, "w", encoding="utf-8") as fh:
                if isinstance(raw, dict):
                    json.dump(raw, fh, ensure_ascii=False, indent=2)
                else:
                    fh.write(str(raw))
            logger.info("saved raw cockpit payload to %s", debug_fn)
        except Exception:
            logger.exception("failed to save debug payload")

    # 3) validate payload type
    if not isinstance(raw, dict):
        preview = str(raw)[:800]
        logger.error("cockpit payload is not JSON object; preview=%s", preview)
        return {"error": "Cockpit payload is not a JSON object", "step": "fetch", "payload_preview": preview}

    # 4) normalize
    try:
        view = _normalize_cockpit(raw, sections)
        logger.info("normalized cockpit view keys=%s", list(view.keys()))
    except Exception as e:
        tb = traceback.format_exc()
        logger.exception("normalize failed: %s", e)
        return {"error": f"Failed to normalize cockpit payload: {e}", "step": "normalize", "trace": tb}

    view["_resolved"] = res
    elapsed = time.time() - start
    logger.info("completed cockpit_get_view_by_sid in %.3fs", elapsed)
    return view


if __name__ == "__main__":
    # asyncio.run(print_tools())
    print("⚡ Starting server with session validation...")
    mcp.run(transport ="streamable-http")
    # mcp.run(transport ="sse")
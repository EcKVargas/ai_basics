def get_weather_schema():

    return [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a given latitude and longitude.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "The latitude of the location to get the weather for.",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "The longitude of the location to get the weather for.",
                        },
                    },
                    "required": ["latitude", "longitude"],
                    "additionalProperties": False,
                },
                "strict": True,
            },

        }
    ]

# tool_schemas/tool_schemas.py


def get_search_system_flexi_schema():
    """Schema for /report/flexi (field-based search, structured)."""
    return {
        "type": "function",
        "function": {
            "name": "search_system_flexi",
            "description": (
                "Query the SLIM Flexi Report API to search SAP system landscape data. "
                "Select which fields to retrieve and apply filters to narrow results. "
                "Each filter uses the pattern 'field|value'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "List of field names to include in the query result. "
                            "Supports dot notation and aliases via 'field as Alias'. "
                            "Example: ['SID', 'systemType', 'status', 'customer.name']"
                        )
                    },
                    "filters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "List of filters to apply in 'field|value' format. "
                            "Example: ['status|Parked', 'systemType|DEV']. "
                            "Do not include SID filters when querying multiple systems."
                            
                        )
                    },
                    "otype": {
                        "type": "string",
                        "enum": ["json", "xml", "csv"],
                        "description": "Output format (default: json)."
                    }
                },
                "required": ["fields" , "filters" ,"otype"],
                "additionalProperties": False
            },
            "strict": True
        }
    }


# def get_entity_details_schema():
#     """
#     Schema for /rest/entityData/get/{entity} supporting:
#       - Systems (model.system.ABAPSystem)
#       - Landscapes (model.Landscape)
#     Filters map to repeated qFieldValue params: field~value
#     Examples:
#       - status=parked: qFieldValue=status~parked
#       - SID=ADL: qFieldValue=SID~ADL
#       - Landscape name=CRM 714: qFieldValue=name~CRM%20714
#       - AND across multiple qFieldValue; OR may require backend-specific encoding.
#     """
#     return {
#         "type": "function",
#         "function": {
#             "name": "get_entity_details",
#             "description": (
#                 "Fetch entity data from /rest/entityData/get/{entity}. "
#                 "Supports systems (model.system.ABAPSystem) and landscapes (model.Landscape). "
#                 "Returns one or many entries depending on filters."
#             ),
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "entity": {
#                         "type": "string",
#                         "enum": ["model.system.ABAPSystem", "model.Landscape"],
#                         "description": "Target entity to query."
#                     },
#                     "filters": {
#                         "type": "array",
#                         "description": (
#                             "List of filters mapped to qFieldValue as 'field~value'. "
#                             "Multiple entries are ANDed by default."
#                         ),
#                         "items": {
#                             "type": "object",
#                             "properties": {
#                                 "field": {
#                                     "type": "string",
#                                     "description": "Entity attribute to match (e.g., 'SID', 'status', 'name', 'product.name', 'usage')."
#                                 },
#                                 "value": {
#                                     "type": "string",
#                                     "description": "Match value; '~' semantics as per backend (typically contains/equals). URL-encode if needed."
#                                 }
#                             },
#                             "required": ["field", "value"],
#                             "additionalProperties": False
#                         }
#                     },
#                     "logic": {
#                         "type": "string",
#                         "enum": ["AND", "OR"],
#                         "description": (
#                             "How to combine filters. Backend natively ANDs repeated qFieldValue. "
#                             "OR may require encoding multiple values per field or backend support."
#                         )
#                     },
#                     "limit": {
#                         "type": "integer",
#                         "minimum": 1,
#                         "description": "Optional client-side limit on returned items."
#                     },
#                     "offset": {
#                         "type": "integer",
#                         "minimum": 0,
#                         "description": "Optional client-side offset (if you implement pagination)."
#                     },
#                     "q_raw": {
#                         "type": "array",
#                         "description": (
#                             "Advanced: pass-through list of raw qFieldValue strings ('field~value'). "
#                             "If provided, these are appended as-is."
#                         ),
#                         "items": {"type": "string"}
#                     }
#                 },
#                 "required": ["entity"],
#                 "additionalProperties": False
#             },
#             "strict": True
#         }
#     }

def get_cockpit_get_view_by_sid_schema():
    return {
        "type": "function",
        "function": {
            "name": "cockpit_get_view_by_sid",
            "description": (
                "Resolve a SID to objectid via Flexi and return a summarized System Cockpit view "
                "(system details, availability, program/landscape). Use this when the user asks "
                "for an overview of a single system (e.g., 'Show ERX overview')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sid": {
                        "type": "string",
                        "description": "3-letter system SID, e.g. 'ERX' or 'ADL'."
                    },
                    "systype": {
                        "type": "string",
                        "enum": ["ABAPSystem"],
                        "description": "Optional hint to disambiguate the SID."
                    },
                    "sections": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "system_details","availability","program_landscape","Clients","Software_Components"
                            ]
                        },
                        "description": "Optional: which sections to include. If omitted, all."
                    }
                },
                "required": ["sid","systype","sections"],
                "additionalProperties": False
            },
            "strict": True
        }
    }


def get_all_schemas():
    """Convenience: return both tool schemas as a list."""
    return [get_search_system_flexi_schema(),  get_cockpit_get_view_by_sid_schema()]

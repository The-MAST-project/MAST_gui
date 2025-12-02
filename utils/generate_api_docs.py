"""
Generate API documentation from @gui_endpoint decorated methods
"""

import inspect
from common.api import ControlApi
from common.decorators import is_gui_endpoint, get_endpoint_capability, get_endpoint_description

def generate_api_docs():
    """Generate markdown documentation of all GUI-exposed endpoints"""
    api = ControlApi()
    
    docs = ["# GUI-Exposed Backend Endpoints\n\n"]
    
    for name, method in inspect.getmembers(api, predicate=inspect.ismethod):
        if is_gui_endpoint(method):
            capability = get_endpoint_capability(method) or "None (all users)"
            description = get_endpoint_description(method)
            sig = inspect.signature(method)
            
            docs.append(f"## `{name}{sig}`\n\n")
            docs.append(f"**Description**: {description}\n\n")
            docs.append(f"**Required Capability**: `{capability}`\n\n")
            docs.append("---\n\n")
    
    return "".join(docs)

if __name__ == "__main__":
    print(generate_api_docs())

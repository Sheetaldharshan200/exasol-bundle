from typing import List, Optional
from exa_bundle.core import ExasolComponent
from exa_bundle.components.personal_db import PersonalDBComponent
from exa_bundle.components.mcp_server import MCPServerComponent
from exa_bundle.components.json_tables import JsonTablesComponent

_COMPONENTS: List[ExasolComponent] = [
    PersonalDBComponent(),
    MCPServerComponent(),
    JsonTablesComponent()
]

def get_all() -> List[ExasolComponent]:
    return _COMPONENTS

def get_by_name(name: str) -> Optional[ExasolComponent]:
    for component in _COMPONENTS:
        if component.name == name:
            return component
    return None
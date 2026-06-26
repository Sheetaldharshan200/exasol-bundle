from typing import List, Optional
from exasol_bundle.core import ExasolComponent
from exasol_bundle.components.personal_db import PersonalDBComponent
from exasol_bundle.components.mcp_server import MCPServerComponent
from exasol_bundle.components.json_tables import JsonTablesComponent

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
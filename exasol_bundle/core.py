from abc import ABC, abstractmethod

class ExasolComponent(ABC):
    """Universal contract for any Exasol tool."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The CLI identifier (e.g., 'mcp', 'personal')."""
        pass

    @abstractmethod
    def install(self) -> None:
        """Logic to fetch external binaries or verify installation."""
        pass

    def start(self) -> None:
        """Logic to run the tool (optional)."""
        print(f"[{self.name}] does not have a start command.")
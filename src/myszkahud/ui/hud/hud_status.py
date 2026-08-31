"""Model statusów modułów w MyszkaHUD."""
from enum import Enum


class ModuleStatus(Enum):
    """Status gotowości modułu aplikacji."""
    READY = "READY"
    WORKING = "WORKING"
    ERROR = "ERROR"
    DISABLED = "DISABLED"

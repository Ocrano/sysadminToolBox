# src/ui/components/__init__.py
"""
Package des composants UI réutilisables
"""

from .common_widgets import (
    VersionLabel,
    ConnectionStatusWidget, 
    ActionButton,
    LogDisplay,
    LogControlPanel,
    SectionHeader,
    ConfigurationGroup,
    ActionGrid,
    WidgetFactory,
    MetricsDisplay,
    StatusTable
)

from .connection_manager import (
    ConnectionManager,
    ConnectionCard,
    ConnectionStatusIndicator
)

__all__ = [
    # Common widgets
    'VersionLabel',
    'ConnectionStatusWidget', 
    'ActionButton',
    'LogDisplay',
    'LogControlPanel',
    'SectionHeader',
    'ConfigurationGroup',
    'ActionGrid',
    'WidgetFactory',
    'MetricsDisplay',
    'StatusTable',
    
    # Connection Manager
    'ConnectionManager',
    'ConnectionCard',
    'ConnectionStatusIndicator'
]
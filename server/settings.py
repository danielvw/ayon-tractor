"""Settings for the Tractor addon."""
from __future__ import annotations
from typing import Any, List

from pydantic import validator

from ayon_server.settings import BaseSettingsModel, SettingsField, ensure_unique_names


class EngineItemSubmodel(BaseSettingsModel):
    """Verbindungsinfo für eine Tractor Engine."""
    _layout = "expanded"
    name: str = SettingsField(title="Engine Name")
    hostname: str = SettingsField(title="Hostname", default="tractor-engine")
    port: int = SettingsField(title="Port", default=80)
    use_password: bool = SettingsField(False, title="Require authentication")
    default_username: str = SettingsField("", title="Default user name")
    default_password: str = SettingsField("", title="Default password")
    default_pool: str = SettingsField("default", title="Default pool")
    default_crew: str = SettingsField("default", title="Default crew")
    default_service: str = SettingsField("PixarRender", title="Default service")


class TractorSettings(BaseSettingsModel):
    """Settings für Tractor Addon."""
    engines: list[EngineItemSubmodel] = SettingsField(
        default_factory=list,
        title="Tractor Engines",
        scope=["studio"],
    )

    selected_engine: str = SettingsField(
        title="Selected Engine",
        section="---",
        scope=["project", "site"],
        description="Select Tractor engine to use for this Project",
    )

    priority: int = SettingsField(
        100,
        title="Default Priority",
        section="---",
        scope=["project", "site"],
        ge=0,
        le=1000,
    )

    @validator("engines")
    def validate_unique_names(cls, value: List[EngineItemSubmodel]) -> List[EngineItemSubmodel]:
        ensure_unique_names(value)
        return value


DEFAULT_VALUES: dict[str, Any] = {
    "engines": [
        {
            "name": "default",
            "hostname": "tractor-engine",
            "port": 80,
            "use_password": False,
            "default_username": "root",
            "default_password": "",
            "default_pool": "default",
            "default_crew": "default",
            "default_service": "PixarRender",
        }
    ],
    "selected_engine": "default",
    "priority": 100,
}
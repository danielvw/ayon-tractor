"""Tractor addon library - dataclasses and helper functions."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class TractorConnectionInfo:
    """Verbindungsinfo für Tractor Engine (analog zu DeadlineConnectionInfo)."""
    hostname: str
    port: int
    user: str = "root"
    password: Optional[str] = None
    use_password: bool = False

    def to_engine_client_params(self) -> Dict[str, Any]:
        """Konvertiert für EngineClient.__init__()."""
        return {
            "hostname": self.hostname,
            "port": self.port,
            "user": self.user,
            "password": self.password,
        }


@dataclass
class TractorJobInfo:
    """JobInfo für Tractor-Submission (analog zu PublishDeadlineJobInfo)."""
    # Generische Felder
    title: str = field(default="Untitled")
    frames: Optional[str] = field(default=None)
    camera: Optional[str] = field(default=None)
    layer: Optional[str] = field(default=None)
    priority: Optional[int] = field(default=None)
    pool: Optional[str] = field(default=None)
    crew: Optional[str] = field(default=None)
    service: Optional[str] = field(default=None)

    # Renderer-spezifisch (wird von Subklasse gefüllt)
    render_cmd: Optional[List[str]] = field(default=None)
    plugin_info: Optional[Dict[str, Any]] = field(default=None)

    # AYON-spezifisch
    project_name: Optional[str] = field(default=None)
    folder_path: Optional[str] = field(default=None)
    task_name: Optional[str] = field(default=None)

    def serialize(self) -> Dict[str, Any]:
        """Serialisiert für Tractor submission."""
        result = {}
        for field_name in [
            "title", "frames", "camera", "layer", "priority",
            "pool", "crew", "service", "render_cmd", "plugin_info",
            "project_name", "folder_path", "task_name"
        ]:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value
        return result


# Arnold families (erweiterbar für RenderMan)
TRACTOR_FAMILIES = [
    "arnold_rop",
    "render.arnold",
]
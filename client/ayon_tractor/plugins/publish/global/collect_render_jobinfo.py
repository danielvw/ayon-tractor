"""Collect Render JobInfo from instance and settings."""
from __future__ import annotations
from typing import TYPE_CHECKING

from ayon_core.pipeline import AYONPyblishPluginMixin
from ayon_core.pipeline.publish import PublishPyblishPluginBase

from ayon_tractor.lib import TRACTOR_FAMILIES, TractorJobInfo

if TYPE_CHECKING:
    from pyblish.api import Context, Instance


class CollectRenderJobInfo(PublishPyblishPluginBase, AYONPyblishPluginMixin):
    """Sammelt JobInfo aus Settings und instance.data.

    Erstellt TractorJobInfo mit generischen Feldern (frames, camera, layer, etc.)
    und speichert in instance.data["tractor"]["job_info"].
    """
    order = 0.420
    label = "Collect Render JobInfo"
    families = TRACTOR_FAMILIES
    targets = ["local"]

    def process(self, instance: Instance) -> None:
        """Erstellt TractorJobInfo und speichert in instance.data."""
        # Hole Settings
        tractor_settings = instance.context.data["project_settings"]["tractor"]
        engine_name = tractor_settings.get("selected_engine", "default")

        # Hole Engine-Config für Default-Werte
        addon = instance.context.data["ayon_addons"].get("tractor")
        if not addon:
            self.log.warning("TractorAddon nicht gefunden. Überspringe.")
            return

        engine_config = addon.engine_configs.get(engine_name)
        if not engine_config:
            self.log.warning(f"Engine '{engine_name}' nicht gefunden. Überspringe.")
            return

        # Hole Werte aus Settings
        priority = tractor_settings.get("priority", 100)
        pool = engine_config.get("default_pool", "default")
        crew = engine_config.get("default_crew", "default")
        service = engine_config.get("default_service", "PixarRender")

        # Hole Werte aus instance.data
        frames = instance.data.get("frames", "")
        camera = instance.data.get("camera", "")
        layer = instance.data.get("layer", "")

        # Hole AYON-spezifische Werte
        project_name = instance.context.data.get("projectName")
        folder_path = instance.data.get("folderPath")
        task_name = instance.data.get("task")

        # Erstelle TractorJobInfo (Punkt 3: verschachteltes Schema)
        job_info = TractorJobInfo(
            title=instance.name,
            frames=frames,
            camera=camera,
            layer=layer,
            priority=priority,
            pool=pool,
            crew=crew,
            service=service,
            project_name=project_name,
            folder_path=folder_path,
            task_name=task_name,
        )

        # Speichere in instance.data
        if "tractor" not in instance.data:
            instance.data["tractor"] = {}
        instance.data["tractor"]["job_info"] = job_info
        instance.data["tractor"]["engine_name"] = engine_name

        self.log.info(f"JobInfo erstellt: {job_info.title}, Frames: {job_info.frames}")
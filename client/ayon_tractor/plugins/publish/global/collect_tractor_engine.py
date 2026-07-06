"""Collect Tractor Engine connection info from settings."""
from __future__ import annotations
from typing import TYPE_CHECKING

from ayon_core.pipeline import AYONPyblishPluginMixin
from ayon_core.pipeline.publish import PublishPyblishPluginBase

from ayon_tractor.lib import TRACTOR_FAMILIES

if TYPE_CHECKING:
    from pyblish.api import Context


class CollectTractorEngine(PublishPyblishPluginBase, AYONPyblishPluginMixin):
    """Sammelt Verbindungsinfo für die Tractor Engine aus Settings.

    WICHTIG: Diese Klasse ruft TractorAddon.get_engine_connection_info()
    auf, um die Verbindungsinfo zu erhalten (keine Duplizierung der Logik).
    """
    order = 0.400
    label = "Collect Tractor Engine"
    families = TRACTOR_FAMILIES
    targets = ["local"]

    def process(self, instance: "Context") -> None:
        """Holt Engine-Verbindungsinfo und speichert in instance.data."""
        # Hole Addon-Instanz
        addon = instance.context.data["ayon_addons"].get("tractor")
        if not addon:
            self.log.warning("TractorAddon nicht gefunden. Überspringe.")
            return

        # Hole Settings für diese Instanz
        tractor_settings = instance.context.data["project_settings"]["tractor"]
        engine_name = tractor_settings.get("selected_engine", "default")

        # Hole Verbindungsinfo über Addon-Methode (Punkt 5: konsolidiert)
        connection_info = addon.get_engine_connection_info(engine_name)

        # Speichere in instance.data (Punkt 3: verschachteltes Schema)
        if "tractor" not in instance.data:
            instance.data["tractor"] = {}
        instance.data["tractor"]["connection_info"] = connection_info

        self.log.info(f"Engine '{engine_name}' konfiguriert: {connection_info.hostname}:{connection_info.port}")
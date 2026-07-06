"""Tractor addon - AYON integration for Pixar Tractor."""
from __future__ import annotations
import os
from typing import TYPE_CHECKING, Optional, Dict, Any, List

from ayon_core.addon import AYONAddon, IPluginPaths
from ayon_core.lib import CacheItem

from .version import __version__
from .lib import TractorConnectionInfo

if TYPE_CHECKING:
    from ayon_server.addons import BaseServerAddon

TRACTOR_ADDON_ROOT = os.path.dirname(os.path.abspath(__file__))


class TractorAddon(AYONAddon, IPluginPaths):
    """AYON Addon für Pixar Tractor Farm Submission."""
    name = "tractor"
    version = __version__

    def initialize(self, studio_settings: Dict[str, Any]) -> None:
        """Initialisiert das Addon mit Studio-Settings."""
        tractor_settings = studio_settings.get(self.name, {})
        engine_configs = {
            config["name"]: config
            for config in tractor_settings.get("engines", [])
        }

        if not engine_configs:
            self.enabled = False
            self.log.warning("Tractor Engine Konfigurationen fehlen. Addon deaktiviert.")
            return

        self.engine_configs = engine_configs
        self._connection_info_cache: Dict[str, TractorConnectionInfo] = {}
        self._local_settings_cache = CacheItem(lifetime=60)

    def get_plugin_paths(self) -> Dict[str, List[str]]:
        """Gibt Plugin-Pfade zurück (global + renderer-spezifisch)."""
        publish_dir = os.path.join(TRACTOR_ADDON_ROOT, "plugins", "publish")
        return {
            "global": [os.path.join(publish_dir, "global")],
            "arnold": [os.path.join(publish_dir, "arnold")],
            "renderman": [os.path.join(publish_dir, "renderman")],
        }

    def get_publish_plugin_paths(
        self,
        host_name: Optional[str] = None
    ) -> List[str]:
        """Gibt Plugin-Pfade für den angegebenen Host zurück.

        ACHTUNG: Im Gegensatz zu ayon-deadline filtern wir nach RENDERER,
        nicht nach Host. Ein Host (z.B. Maya) kann sowohl Arnold als auch
        RenderMan rendern.

        Args:
            host_name: Wird ignoriert (für Kompatibilität mit IPluginPaths)

        Returns:
            List[str]: Pfade zu global/ und renderer-spezifischen Verzeichnissen
        """
        publish_dir = os.path.join(TRACTOR_ADDON_ROOT, "plugins", "publish")
        paths = [
            os.path.join(publish_dir, "global"),
            os.path.join(publish_dir, "arnold"),
        ]
        return paths

    def get_engine_connection_info(
        self,
        engine_name: str,
        local_settings: Optional[Dict[str, Any]] = None
    ) -> TractorConnectionInfo:
        """Holt Verbindungsinfo für eine Tractor Engine.

        Args:
            engine_name: Name der Engine aus Settings
            local_settings: Lokale Einstellungen (optional)

        Returns:
            TractorConnectionInfo: Verbindungsparameter für EngineClient
        """
        engine_config = self.engine_configs.get(engine_name)
        if not engine_config:
            raise ValueError(f"Engine '{engine_name}' nicht gefunden in {list(self.engine_configs.keys())}")

        # Prüfe lokale Settings (überschreiben Studio-Settings)
        if local_settings is None:
            local_settings = self._get_local_settings()

        # Hole Username/Password aus lokalen Settings oder Studio-Settings
        username = engine_config.get("default_username", "root")
        password = engine_config.get("default_password")
        use_password = engine_config.get("use_password", False)

        # Lokale Settings überschreiben
        for local_info in local_settings.get("local_settings", []):
            if local_info.get("engine_name") == engine_name:
                if local_info.get("username"):
                    username = local_info["username"]
                if local_info.get("password"):
                    password = local_info["password"]
                break

        hostname = engine_config.get("hostname", "tractor-engine")
        port = engine_config.get("port", 80)

        return TractorConnectionInfo(
            hostname=hostname,
            port=port,
            user=username,
            password=password,
            use_password=use_password,
        )

    def _get_local_settings(self) -> Dict[str, Any]:
        """Holt lokale Addon-Settings (caching)."""
        if not self._local_settings_cache.is_valid:
            try:
                from ayon_api import get_server_api_connection
                con = get_server_api_connection()
                self._local_settings_cache.update_data(
                    con.get_addon_site_settings(self.name, self.version)
                )
            except Exception:
                self._local_settings_cache.update_data({"local_settings": []})
        return self._local_settings_cache.get_data()
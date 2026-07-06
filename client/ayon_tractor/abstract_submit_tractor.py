"""Abstract base class for Tractor job submission.

Diese Klasse ist die Basisklasse für alle Tractor-Submission-Plugins.
Sie implementiert die renderer-agnostische Logik (Verbindung, Job-Erstellung, Spooling).

WICHTIG: Diese Klasse nutzt AbstractMetaInstancePlugin als Metaclass (ayon-core-Muster).
         @abstractmethod wirkt dann echte Durchsetzung.
"""
from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, List, Dict, Any

from ayon_core.pipeline import AYONPyblishPluginMixin
from ayon_core.pipeline.publish import PublishPyblishPluginBase

from ayon_tractor.lib import TRACTOR_FAMILIES

if TYPE_CHECKING:
    from pyblish.api import Instance
    from ayon_tractor.tractor.api.author import Job, Task, Command


# Importiere AbstractMetaInstancePlugin aus ayon-core
try:
    from ayon_core.pipeline.publish.publish_plugins import AbstractMetaInstancePlugin
except ImportError:
    # Fallback: Wenn AbstractMetaInstancePlugin nicht existiert, nutze ABCMeta direkt
    AbstractMetaInstancePlugin = ABCMeta


class AbstractSubmitTractor(
    PublishPyblishPluginBase,
    AYONPyblishPluginMixin,
    metaclass=AbstractMetaInstancePlugin
):
    """Basisklasse für Tractor Job-Submission.

    Diese Klasse ist komplett renderer-agnostisch:
    - Keine ASS-Datei- oder kick-Logik
    - Keine hardcodierten Pfade
    - Keine renderer-spezifischen Befehle

    Alle renderer-spezifischen Teile gehören in Subklassen (z.B. SubmitArnoldJob).

    ACHTUNG: AYONPyblishPluginMixin (aus ayon-core) nutzt NICHT ABCMeta als Metaclass.
             Diese Klasse nutzt AbstractMetaInstancePlugin für echte @abstractmethod-Durchsetzung.

    Subklassen MÜSSEN folgende Methoden implementieren:
    - get_job_info()
    - get_service()
    - get_render_cmd()

    get_plugin_info() ist optional (bei Tractor wird PluginInfo im render_cmd übertragen).
    """

    label = "Submit to Tractor"
    order = 0.610  # IntegratorOrder + 0.1
    families = TRACTOR_FAMILIES
    targets = ["local"]

    # --- Abstract Methods (müssen in Subklasse implementiert werden) ---

    @abstractmethod
    def get_job_info(self, job: Job) -> Job:
        """Füllt JobInfo mit renderer-spezifischen Werten.

        Args:
            job: author.Job-Objekt (Tractor-API)

        Returns:
            Job: Das befüllte Job-Objekt
        """
        raise NotImplementedError("get_job_info() muss in Subklasse implementiert werden")

    def get_plugin_info(self) -> Dict[str, Any]:
        """Erstellt PluginInfo für den spezifischen Renderer.

        WICHTIG: Bei Tractor wird PluginInfo NICHT als separates JSON-Feld
        übertragen. Die Plugin-spezifischen Informationen sind im render_cmd
        (argv) enthalten (z.B. 'kick -i file.ass' für Arnold).

        Diese Methode ist optional und kann überschrieben werden, z.B. für
        spätere Erweiterungen oder Metadaten.

        Returns:
            Dict[str, Any]: Plugin-Info Dict (z.B. {"Asset": "ass", "File": "file.ass"})
        """
        return {}

    @abstractmethod
    def get_service(self) -> str:
        """Gibt den Tractor service-String zurück.

        Returns:
            str: Service-String (z.B. "PixarRender" für Arnold)
        """
        raise NotImplementedError("get_service() muss in Subklasse implementiert werden")

    @abstractmethod
    def get_render_cmd(self) -> List[str]:
        """Gibt den Befehl für den Render-Task zurück.

        Returns:
            List[str]: Argv-Liste (z.B. ["/usr/bin/kick", "-i", "file.ass"])
        """
        raise NotImplementedError("get_render_cmd() muss in Subklasse implementiert werden")

    # --- Helper Methods (in Basisklasse implementiert) ---

    def get_engine_client(self) -> "EngineClient":
        """Erstellt EngineClient aus connection_info.

        Returns:
            EngineClient: Verbindungsobjekt zur Tractor Engine
        """
        from ayon_tractor.tractor.base import EngineClient

        connection_info = self.tractor_job_info.connection_info
        params = connection_info.to_engine_client_params()

        client = EngineClient(**params)
        client.open()
        return client

    def create_job(self, title: str) -> Job:
        """Erstellt author.Job mit generischen Attributen.

        Args:
            title: Job-Titel

        Returns:
            Job: Neues author.Job-Objekt
        """
        from ayon_tractor.tractor.api.author import Job

        job = Job(title=title)
        return job

    def create_task(self, title: str, argv: List[str], service: str) -> Task:
        """Erstellt author.Task mit author.Command.

        Args:
            title: Task-Titel
            argv: Command-Argv
            service: Service-String

        Returns:
            Task: Neues author.Task-Objekt
        """
        from ayon_tractor.tractor.api.author import Task

        task = Task(title=title, argv=argv, service=service)
        return task

    def submit(self, job: Job) -> str:
        """Spoolt Job an Engine, gibt JID zurück.

        Args:
            job: author.Job-Objekt

        Returns:
            str: Job-ID (JID)
        """
        # Hole EngineClient
        engine_client = self.get_engine_client()

        # Spool Job (als JSON)
        result = engine_client.spool(job.asJSON(), skipLogin=True, block=False, format="JSON")

        # Parse JID aus Antwort
        import json
        result_dict = json.loads(result)
        jid = result_dict.get("jid")

        return str(jid)

    # --- Main Entry Point ---

    def process(self, instance: Instance) -> None:
        """Eintrittspunkt: Engine-Client holen, Job erstellen, submit.

        Ablauf:
        1. tractor_job_info = instance.data["tractor"]["job_info"]  # TractorJobInfo (Collector)
        2. job = author.Job(title=...)                              # author.Job (Tractor-API)
        3. job = self.get_job_info(job)                             # Subklasse befüllt
        4. job.spool()                                              # Überträgt an Engine
        """
        # Hole TractorJobInfo aus Collector (Punkt 3: verschachteltes Schema)
        if "tractor" not in instance.data:
            raise RuntimeError("Keine 'tractor'-Daten in instance.data. CollectTractorEngine fehlt?")
        if "job_info" not in instance.data["tractor"]:
            raise RuntimeError("Keine 'job_info' in instance.data['tractor']. CollectRenderJobInfo fehlt?")

        self.tractor_job_info = instance.data["tractor"]["job_info"]
        self.tractor_job_info.connection_info = instance.data["tractor"]["connection_info"]

        # Erstelle author.Job (Punkt 4: Objektfluss)
        job = self.create_job(self.tractor_job_info.title)

        # Befülle Job mit renderer-spezifischen Werten
        job = self.get_job_info(job)

        # Erstelle Task mit Render-Befehl
        service = self.get_service()
        render_cmd = self.get_render_cmd()
        task = self.create_task("Render", render_cmd, service)
        job.addChild(task)

        # Spool Job an Engine
        jid = self.submit(job)

        # Speichere JID in instance.data für nachgelagerte Plugins
        instance.data["tractorSubmissionJob"] = {
            "jid": jid,
            "service": service,
        }

        self.log.info(f"Job '{job.title}' gespoolt mit JID: {jid}")
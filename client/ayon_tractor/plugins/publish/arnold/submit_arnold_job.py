"""Submit Arnold Job to Tractor.

Dieses Plugin implementiert die Arnold-spezifische Logik für Tractor-Submission.
Alle Arnold-spezifischen Teile (ASS-Datei, kick-Befehl, PixarRender-Service)
gehören hierher.

Die Basisklasse (AbstractSubmitTractor) bleibt komplett renderer-agnostisch.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any

from ayon_tractor.abstract_submit_tractor import AbstractSubmitTractor

if TYPE_CHECKING:
    from tractor.api.author import Job


class SubmitArnoldJob(AbstractSubmitTractor):
    """Arnold-spezifische Tractor-Submission.

    Verantwortung (nur Arnold-spezifische Logik):
    - get_job_info(): Füllt JobInfo mit Arnold-spezifischen Werten (service="PixarRender")
    - get_plugin_info(): Erstellt Arnold PluginInfo (ASS-Datei-Pfad, kick-Optionen)
    - get_service(): Gibt "PixarRender" zurück
    - get_render_cmd(): Gibt ["kick", "-i", "file.ass", ...] zurück
    """

    label = "Submit Arnold Job to Tractor"
    order = 0.610  # IntegratorOrder + 0.1
    families = ["arnold_rop", "render.arnold"]
    targets = ["local"]

    def get_job_info(self, job: Job) -> Job:
        """Setzt Arnold-spezifische Job-Attribute.

        Args:
            job: author.Job-Objekt

        Returns:
            Job: Das befüllte Job-Objekt
        """
        # Setze service für Arnold (PixarRender)
        job.service = self.get_service()

        # Setze Crew (aus TractorJobInfo)
        if self.tractor_job_info.crew:
            job.crews = [self.tractor_job_info.crew]

        # Setze Priority (aus TractorJobInfo)
        if self.tractor_job_info.priority:
            job.priority = self.tractor_job_info.priority

        # TODO: DirMap für Pfad-Mapping (Pfadkonvertierung)
        # Aktuell hardcodiert für X:/ -> /cglab-store/projects
        # Sollte durch AYONs Anatomy-System ersetzt werden
        # job.newDirMap(src="X:/", dst="/cglab-store/projects", zone="UNC")

        return job

    def get_plugin_info(self) -> Dict[str, Any]:
        """Erstellt Arnold PluginInfo.

        Returns:
            Dict[str, Any]: Plugin-Info Dict
        """
        # Hole ASS-Datei-Pfad aus instance.data
        ass_file_path = self.tractor_job_info.plugin_info.get("File", "") if self.tractor_job_info.plugin_info else ""

        return {
            "Asset": "ass",
            "File": ass_file_path,
            "Version": "6.2.0.1",  # Arnold version (anpassbar)
        }

    def get_service(self) -> str:
        """Gibt den Arnold service-String zurück.

        Returns:
            str: "PixarRender"
        """
        return "PixarRender"

    def get_render_cmd(self) -> List[str]:
        """Gibt den Arnold kick-Befehl zurück.

        Returns:
            List[str]: Argv-Liste für kick
        """
        # Hole ASS-Datei-Pfad
        ass_file_path = self.tractor_job_info.plugin_info.get("File", "") if self.tractor_job_info.plugin_info else ""

        return [
            "/usr/autodesk/arnold/maya2025/bin/kick",
            "-nstdin",
            "-l", "/usr/autodesk/arnold/maya2025/procedurals",
            "-i", ass_file_path,
            "-dw", "-dp",
            "-v", "2"
        ]
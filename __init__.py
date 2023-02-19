# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

"""Metadata plugin based on gexiv2 (https://wiki.gnome.org/Projects/gexiv2) backend.

Properties:
- Gnome dependencies.
- Formatted Metadata.
- Reads Exif, IPTC and XMP.
"""

import contextlib
from typing import Any, Sequence, Iterable

from vimiv.imutils import metadata
from vimiv.utils import log, is_hex

import gi

gi.require_version("GExiv2", "0.10")
from gi.repository import GExiv2 as gexiv2

_logger = log.module_logger(__name__)


class MetadataGexiv2(metadata.MetadataPlugin):
    """Provides metadata support based on gexiv2.

    Implements `get_metadata`, `get_keys`, `copy_metadata`, and `get_date_time`.
    """

    def __init__(self, path: str) -> None:
        self._path = path

        try:
            self._metadata = gexiv2.Metadata(path)
        except gi.repository.GLib.GError:
            _logger.debug("File %s not found", path)
            self._metadata = None

    @property
    def name(self) -> str:
        """Get the name of the used backend."""
        return "gexiv2"

    @property
    def version(self) -> str:
        """Get the version of the used backend."""
        return "0.10"

    def get_metadata(self, desired_keys: Sequence[str]) -> metadata.MetadataDictT:
        """Get value of all desired keys for the current image."""
        out = {}

        if self._metadata is None:
            return {}

        for key in desired_keys:
            try:
                out[key] = (
                    self._metadata.try_get_tag_label(key),
                    self._metadata.try_get_tag_interpreted_string(key),
                )
            except gi.repository.GLib.GError:
                _logger.debug("Key %s is invalid for the current image", key)

        return out

    def get_keys(self) -> Iterable[str]:
        """Get the keys for all metadata values available for the current image."""
        if self._metadata is None:
            return iter([])

        return (key for key in self._metadata if not is_hex(key.rpartition(".")[2]))

    def copy_metadata(self, dest: str, reset_orientation: bool = True) -> bool:
        """Copy metadata from the current image to dest image."""
        if self._metadata is None:
            return False

        if reset_orientation:
            with contextlib.suppress(KeyError):
                self._metadata.set_orientation(metadata.ExifOrientation.Normal)

        try:
            self._metadata.save_file(dest)
            return True

        # TODO error handling
        except gi.repository.GLib.GError as e:
            _logger.debug("Failed to write metadata for '%s': '%s'", dest, str(e))
        return False

    def get_date_time(self) -> str:
        """Get creation date and time of the current image as formatted string."""
        if self._metadata is None:
            return ""

        with contextlib.suppress(gi.repository.GLib.GError):
            return self._metadata.get_tag_raw("Exif.Image.DateTime")
        return ""


def init(*_args: Any, **_kwargs: Any) -> None:
    metadata.register(MetadataGexiv2)

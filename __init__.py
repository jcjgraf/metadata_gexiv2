# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

"""Utility functions and classes for exif handling.

All exif related tasks are implemented in this module. The heavy lifting is done using
one of the supported exif libraries, i.e.
* piexif (https://pypi.org/project/piexif/) and
* pyexiv2 (https://pypi.org/project/py3exiv2/).
"""

import contextlib
from typing import Any, Sequence, Iterable

from vimiv.imutils import exif
from vimiv.utils import log, lazy, is_hex

import gi

gi.require_version("GExiv2", "0.10")
from gi.repository import GExiv2 as gexiv2

_logger = log.module_logger(__name__)


class ExifHandlerGexiv(exif._ExifHandlerBase):
    """Main ExifHandler implementation based on gexiv2."""

    MESSAGE_SUFFIX = " by gexiv2."

    def __init__(self, filename=""):
        super().__init__(filename)
        try:
            self._metadata = gexiv2.Metadata(filename)
        except gi.repository.GLib.GError:
            _logger.debug("File %s not found", filename)

    def get_formatted_exif(self, desired_keys: Sequence[str]) -> exif.ExifDictT:
        exif = {}

        for base_key in desired_keys:
            # For backwards compability, assume it has one of the following prefixes
            for prefix in ["", "Exif.Image.", "Exif.Photo."]:
                key = f"{prefix}{base_key}"
                try:
                    exif[key] = (
                        self._metadata.try_get_tag_label(key),
                        self._metadata.try_get_tag_interpreted_string(key),
                    )
                    break

                except gi.repository.GLib.GError:
                    _logger.debug("Key %s is invalid for the current image", key)

        return exif

    def get_keys(self) -> Iterable[str]:
        return (key for key in self._metadata if not is_hex(key.rpartition(".")[2]))

    def copy_exif(self, dest: str, reset_orientation: bool = True) -> None:
        if reset_orientation:
            with contextlib.suppress(KeyError):
                self._metadata.set_orientation(exif.ExifOrientation.Normal)
        try:
            self._metadata.save_file(dest)

            _logger.debug("Successfully wrote exif data for '%s'", dest)

        # TODO error handling
        except gi.repository.GLib.GError as e:
            _logger.debug("Failed to write exif data for '%s': '%s'", dest, str(e))

    def exif_date_time(self) -> str:
        with contextlib.suppress(gi.repository.GLib.GError):
            return self._metadata.get_tag_raw("Exif.Image.DateTime")
        return ""


def init(*_args: Any, **_kwargs: Any) -> None:
    exif.set_handler(ExifHandlerGexiv)

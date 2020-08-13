#!/usr/bin/env python3
"""The experimental shooting range"""

# from collections import OrderedDict
from pathlib import Path
import json
import pprint
import sys

import gi

gi.require_version("Gtk", "3.0")
# pylint: disable=wrong-import-position
from gi.repository import Gtk   # noqa: E402


DEFAULT_CDDA_DIR = Path(__file__).parent.joinpath(
        "..", "Cataclysm-DDA", "data", "json")


def load_cdda_data(type_filter=None):
    """Loads the CDDA JSON data files into a dict.

    returns a dict with the members
        { "data": dict, "errors": list, "blob_to_filename": dict }

    'data' is a list with all the data blobs as deserialized
    'errors' is a list of errors found while parsing
    'blob_to_filename' is a dict with blob "id" to filename mapping"""

    data = []
    errors = []
    blob_to_filename = {}
    for jsonfile in DEFAULT_CDDA_DIR.glob("**/*.json"):
        filename = jsonfile.resolve().absolute()
        try:
            with open(filename) as jfile:
                blobs = json.load(jfile)  # , object_pairs_hook=OrderedDict)
        except Exception as err:
            errors.append("Cannot read %s: %s" % (filename, err))
        for blob in blobs:
            if isinstance(blob, dict):
                blob_type = blob.get("type")
                if type_filter and blob_type not in type_filter:
                    continue
                blob_id = blob.get("id")
                if not blob_id:
                    continue
                if isinstance(blob_id, list):
                    blob_id = "_".join(blob_id)
                blob_to_filename[blob_id] = filename
            data.append(blob)
    return {
        "data": data,
        "errors": errors,
        "blob_to_filename": blob_to_filename
    }


def create_window():
    """Creates the main window and sets up event handlers."""
    window = Gtk.Window(title="Shooting Range")
    window.connect("destroy", Gtk.main_quit)

    # label = Gtk.label("The Shooting Range")
    # window.add(label)

    # label.show()
    window.show()


if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=2)
    base_data = load_cdda_data(type_filter=["GUN", "MAGAZINE", "AMMO", "AMMO_TYPES"])
    create_window()
    Gtk.main()
    # pp.pprint(base_data)

"""Configuration loading for the service."""

import tomllib
from pathlib import Path


def load_config(path):
    """Load and return the TOML configuration at *path*.

    TOML is the service's configuration format.  The returned value is the
    parsed document (a dictionary); values and nested tables are left as
    authored in the file.  File and TOML parsing errors are allowed to
    propagate so callers get the usual, actionable exceptions.
    """
    with Path(path).open("rb") as config_file:
        return tomllib.load(config_file)

import os
import tomllib


def load_config(path):
    """Load a TOML configuration file, applying supported environment overrides."""
    with open(path, "rb") as config_file:
        config = tomllib.load(config_file)

    service_port = os.environ.get("SERVICE_PORT")
    if service_port is not None:
        config.setdefault("service", {})["port"] = int(service_port)

    return config

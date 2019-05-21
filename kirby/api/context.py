import os
from smart_getenv import getenv
import json
from copy import deepcopy

TYPES = {"str": str, "list": list}

KIRBY_ENV_SIGNATURE = "KIRBY_ENV_SIGNATURE"


def parse_types(config):
    config = deepcopy(config)
    for var, config_keys in config.items():
        for key, value in config_keys.items():
            if key == "type":
                config[var][key] = str(value).split("'")[1]
    return config


def unparse_types(config):
    config = deepcopy(config)
    for var, config_keys in config.items():
        for key, value in config_keys.items():
            if key == "type":
                config[var][key] = TYPES[value]
    return config


class ContextManager:
    def __init__(self, config):
        self.config = config
        return

    def load(self):
        encoder = json.JSONEncoder()
        os.environ[KIRBY_ENV_SIGNATURE] = encoder.encode(
            parse_types(self.config)
        )


class Context:
    def get_signature(self):
        decoder = json.JSONDecoder()
        return unparse_types(decoder.decode(os.environ[KIRBY_ENV_SIGNATURE]))

    def __getattr__(self, item):
        signature = self.get_signature()[item]
        return getenv(item, **signature)

    def __repr__(self):
        all_signatures = self.get_signature()
        return "; ".join(
            [
                f"{var}={repr(getenv(var, **signature))}"
                for var, signature in all_signatures.items()
            ]
        )


ctx = Context()

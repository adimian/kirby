import os
from smart_getenv import getenv
import pickle
import codecs

KIRBY_ENV_SIGNATURE = "__KIRBY_ENV_SIGNATURE"


class MissingEnvironmentVariable(Exception):
    pass


class ContextManager:
    def __init__(self, config):
        self.config = config
        os.environ[KIRBY_ENV_SIGNATURE] = codecs.encode(
            pickle.dumps(self.config), "base64"
        ).decode()


def get_signature():
    kirby_env_signature = os.getenv(KIRBY_ENV_SIGNATURE)
    if kirby_env_signature:
        return pickle.loads(
            codecs.decode(os.getenv(KIRBY_ENV_SIGNATURE).encode(), "base64")
        )
    else:
        return {}


class Context:
    def __getattr__(self, item):
        signature = get_signature().get(item, {})
        attr = getenv(item, **signature)
        if attr:
            return attr
        else:
            raise MissingEnvironmentVariable(
                f"The environment variable {item} hasn't been initialized."
            )

    def __repr__(self):
        all_signatures = get_signature()
        return "; ".join(
            [
                f"{var}={repr(getenv(var, **signature))}"
                for var, signature in all_signatures.items()
            ]
        )

    def __getitem__(self, item):
        return self.__getattr__(item)


ctx = Context()

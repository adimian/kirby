import os
from smart_getenv import getenv
import pickle
import codecs

KIRBY_ENV_SIGNATURE = "__KIRBY_ENV_SIGNATURE"


class ContextManager:
    def __init__(self, config):
        self.config = config
        return

    def load(self):
        os.environ[KIRBY_ENV_SIGNATURE] = codecs.encode(
            pickle.dumps(self.config), "base64"
        ).decode()


def get_signature():
    return pickle.loads(
        codecs.decode(os.environ[KIRBY_ENV_SIGNATURE].encode(), "base64")
    )


class Context:
    def __getattr__(self, item):
        signature = get_signature()[item]
        return getenv(item, **signature)

    def __repr__(self):
        all_signatures = get_signature()
        return "; ".join(
            [
                f"{var}={repr(getenv(var, **signature))}"
                for var, signature in all_signatures.items()
            ]
        )


ctx = Context()

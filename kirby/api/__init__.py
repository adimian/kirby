import requests

from .context import ContextManager, ctx


class Kirby:
    def __init__(self, env_signature, session=None):
        ctx_manager = ContextManager(env_signature)
        ctx_manager.load()
        self.ctx = ctx
        self._session = session or requests.session()

        self._register()

    def get_topic_id(self, topic_name):
        result = self._session.get(
            "/".join([self.ctx.KIRBY_WEB_SERVER, "topic"]),
            params={"name": topic_name},
        )
        assert result.status_code == 200
        return result.json()["id"]

    def _register(self, params=None):
        if not params:
            params = {}

        # If there is a key not in {"source_id", "destination_id"}
        if params.keys() - {"source_id", "destination_id"}:
            raise ValueError(
                "There is at least one key in 'params' that is not accepted. "
                f"'params' can only contains : 'source_id' and 'destination_id'"
            )

        result = self._session.patch(
            "/".join([self.ctx.KIRBY_WEB_SERVER, "registration"]),
            params=dict(**params, **{"script_id": self.ctx.ID}),
        )
        assert result.status_code == 200

    def add_source(self, source):
        self._register({"source_id": self.get_topic_id(source.topic_name)})

    def add_destination(self, destination):
        self._register(
            {"destination_id": self.get_topic_id(destination.topic_name)}
        )

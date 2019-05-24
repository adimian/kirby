import requests

from .context import ContextManager


class Kirby:
    def __init__(self, env_signature, session=None):
        ctx_manager = ContextManager(env_signature)
        ctx_manager.load()

        from .context import ctx

        self.ctx = ctx
        self._session = session or requests.session()

        self._register()

    def _register(self, params=None):
        if not params:
            params = {}

        result = self._session.patch(
            "/".join([self.ctx.KIRBY_WEB_SERVER, "registration"]),
            params=dict(**params, **{"script_id": self.ctx.ID}),
        )
        assert result.status_code == 200

    def _add_source_or_destination(self, ext, key):
        assert key in [
            "source_id",
            "destination_id",
        ], "The key passed as argument must be either 'source_id' or 'destination_id'"

        ext_name = ext.topic_name

        result_get_id = self._session.get(
            "/".join([self.ctx.KIRBY_WEB_SERVER, "topic"]),
            params={"name": ext_name},
        )
        assert result_get_id.status_code == 200
        self._register({key: result_get_id.json()["id"]})

    def add_source(self, source):
        self._add_source_or_destination(source, "source_id")

    def add_destination(self, destination):
        self._add_source_or_destination(destination, "destination_id")

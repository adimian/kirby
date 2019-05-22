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

    def _register(self):
        result = self._session.patch(
            "/".join([self.ctx.KIRBY_WEB_SERVER, "registration"]),
            params={"script_id": self.ctx.ID},
        )
        assert result.status_code == 200

import requests
import logging

from .context import ContextManager, ctx

logger = logging.getLogger(__name__)


class ServerError(BaseException):
    pass


class ClientError(BaseException):
    pass


class Kirby:
    def __init__(self, env_signature, session=None):
        ContextManager(env_signature)
        self.ctx = ctx
        self._session = session or requests.session()

        self._register()

    def get_topic_id(self, topic_name):
        result = self._session.get(
            "/".join([self.ctx.KIRBY_WEB_SERVER, "topic"]),
            params={"name": topic_name},
        )
        if result.status_code != 200:
            if result.status_code == 500:
                raise ServerError("There is an issue with the web server.")
            else:
                raise ClientError(
                    f"There is no id from the name {topic_name}. "
                    f"Verify that the topic has been registered."
                )
        return result.json()["id"]

    def _register(self, source_id=None, destination_id=None):
        params = {"script_id": self.ctx.ID}
        if source_id:
            params.update({"source_id": source_id})
        if destination_id:
            params.update({"destination_id": destination_id})

        result = self._session.patch(
            "/".join([self.ctx.KIRBY_WEB_SERVER, "registration"]), data=params
        )

        if result.status_code != 200:
            if result.status_code == 500:
                raise ServerError("There is an issue with the web server.")
            else:
                raise ClientError("There is an error with the id(s) given.")

    def add_source(self, source):
        self._register(source_id=self.get_topic_id(source.name))

    def add_destination(self, destination):
        self._register(destination_id=self.get_topic_id(destination.name))

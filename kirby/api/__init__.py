import logging
import requests
from urllib.parse import urljoin

from .context import ContextManager, ctx

logger = logging.getLogger(__name__)


class ServerError(BaseException):
    pass


class ClientError(BaseException):
    pass


class Kirby:
    def __init__(self, env_signature, session=None, testing=False):
        ContextManager(env_signature)
        self.testing = testing
        if not testing:
            self._session = session or requests.session()
            self._register()

    def get_topic_id(self, topic_name):
        if not self.testing:
            result = self._session.get(
                urljoin(ctx.KIRBY_WEB_SERVER, "topic"),
                params={"name": topic_name},
            )
            if result.status_code != 200:
                if result.status_code in range(500, 600):
                    raise ServerError("There is an issue with the web server.")
                else:
                    raise ClientError(
                        f"There is no id from the name {topic_name}. "
                        "Verify that the topic has been registered."
                    )
            return result.json()["id"]
        else:
            raise NotImplementedError(
                f"The app has been initialized in testing mode. "
                "You cannot find any id without connection."
            )

    def _register(self, source_id=None, destination_id=None):
        params = {"script_id": ctx.ID}
        if source_id:
            params.update({"source_id": source_id})
        if destination_id:
            params.update({"destination_id": destination_id})

        result = self._session.patch(
            urljoin(ctx.KIRBY_WEB_SERVER, "registration"), data=params
        )

        if result.status_code != 200:
            if result.status_code == 500:
                raise ServerError("There is an issue with the web server.")
            else:
                raise ClientError("There is an error with the id(s) given.")

    def add_source(self, source):
        if not self.testing:
            self._register(source_id=self.get_topic_id(source.name))
        else:
            logger.info(
                f"add_source has been skipped, since app has been "
                "initialized in testing mode"
            )

    def add_destination(self, destination):
        if not self.testing:
            self._register(destination_id=self.get_topic_id(destination.name))
        else:
            logger.info(
                f"add_destination has been skipped, since app has been "
                "initialized in testing mode"
            )

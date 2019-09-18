import logging
import requests
import tenacity
from smart_getenv import getenv
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

RETRIES = getenv("EXT_RETRIES", type=int, default=3)
WAIT_BETWEEN_RETRIES = getenv(
    "EXT_WAIT_BETWEEN_RETRIES", type=float, default=0.4
)


class WebClientError(Exception):
    pass


webserver_retry_decorator = tenacity.retry(
    retry=tenacity.retry_if_exception_type(WebClientError),
    wait=tenacity.wait_fixed(WAIT_BETWEEN_RETRIES),
    stop=tenacity.stop_after_attempt(RETRIES),
    reraise=True,
)


class WebClient:
    def __init__(self, name, web_endpoint_base, session=None):
        self.name = name
        self.web_endpoint_base = web_endpoint_base
        self._session = session or requests.session()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()

    def _request_decorator(self, method):
        def request(endpoint, **kwargs):
            result = method(
                urljoin(self.web_endpoint_base, endpoint), **kwargs
            )

            if result.status_code == 200:
                return result.json()
            raise WebClientError(
                f"{method} error on {result.url}. "
                f"Status code : {result.status_code}. "
                f"Response : {result.text}"
            )

        return webserver_retry_decorator(request)

    def __getattr__(self, item):
        method = getattr(self._session, item)
        if callable(method):
            return self._request_decorator(method)
        else:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{item}'"
            )

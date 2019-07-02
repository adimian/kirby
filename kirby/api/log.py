from .queue import Queue

LOGGER_TOPIC_NAME = "_logs"


class Logger:
    def __init__(self):
        self.queue = Queue(LOGGER_TOPIC_NAME)
        self.name = __name__

    def _send_log_factory(self, level):
        if level == "log":
            level = "noset"

        def send_log(message):
            self.queue.send(
                message, headers={"level": level, "name": self.name}
            )

        return send_log

    def __getattr__(self, item):
        if item in ["critical", "error", "warning", "info", "debug", "log"]:
            return self._send_log_factory(item)

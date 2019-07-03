from .queue import Queue

LOGGER_TOPIC_NAME = "_logs"


class Logger:
    # Logger is an adapter to a Queue
    # It is intended to imitate the behaviour of logger in the standard
    # library. There is 6 levels in the standard library:
    # CRITICAL  >   ERROR   >  WARNING  >   INFO    >   DEBUG   >   NOTSET

    def __init__(self, default_level="noset"):
        self.queue = Queue(LOGGER_TOPIC_NAME)
        self.name = __name__
        self.default_level = default_level

    def _send_log_factory(self, level):
        # Each time a level of log is called the factory is called to
        # create the right function to call.
        # To log with the default log level, the function log can be
        # called.
        if level == "log":
            level = self.default_level

        def send_log(message):
            self.queue.send(
                message, headers={"level": level, "name": self.name}
            )

        return send_log

    def __getattr__(self, item):
        if item in ["critical", "error", "warning", "info", "debug", "log"]:
            return self._send_log_factory(item)

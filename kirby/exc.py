class CoolDownException(Exception):
    """
        triggered when submitting a job more than once during the wakeup window
    """

    pass


class ConfigException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

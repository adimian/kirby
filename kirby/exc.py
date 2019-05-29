class CoolDownException(Exception):
    """
        triggered when submitting a job more than once during the wakeup window
    """

    pass

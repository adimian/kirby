import datetime
import os
import random
import time

from unittest import mock

result_folder = os.path.join(os.path.dirname(__file__), "results")


def mock_webclient(name, get=None):
    mocking_webclient = mock.patch("kirby.ext.webclient.WebClient").__enter__()

    export_data = export_data_constructor(name)

    webclient_obj = mocking_webclient.return_value.__enter__.return_value
    webclient_obj.name = name

    # Mocking functions
    webclient_obj.post = export_data
    webclient_obj.update = export_data
    if get:
        webclient_obj.get = get


def export_data_constructor(path):
    def export_data(*args, **kargs):
        time.sleep(random.uniform(0.5, 1.5))
        now = datetime.datetime.utcnow()

        formatted_args = [a.__repr__() for a in args]
        formatted_kargs = [f"({a}, {b})" for a, b in kargs.items()]
        with open(
            os.path.join(result_folder, path, now.isoformat()), "w+"
        ) as f:
            f.write("(" + ", ".join(formatted_args) + ")")
            f.write("{" + "; ".join(formatted_kargs) + "}")

    return export_data

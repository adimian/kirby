if __name__ == "__main__":
    import os
    import time

    print("Started process")

    time.sleep(2)
    print(os.environ["KIRBY_TEST_MARKER"])

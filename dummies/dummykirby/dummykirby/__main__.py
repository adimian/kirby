if __name__ == "__main__":
    import kirby
    import time

    print("Started process")

    time.sleep(2)
    print(kirby.api.ctx["KIRBY_TEST_MARKER"])

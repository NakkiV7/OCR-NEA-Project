import time


class RunTimer:
    def __init__(self):
        #initial timer state
        self.reset()

    def reset(self):
        #clear timer
        self.start_time = None
        self.end_time = None
        self.running = False

    def start(self):
        #begin run
        self.start_time = time.time()
        self.end_time = None
        self.running = True

    def stop(self):
        #stop run
        if self.running:
            self.end_time = time.time()
            self.running = False

    def elapsed(self):
        #elapsed seconds
        if self.start_time is None:
            return 0.0
        if self.running:
            return time.time() - self.start_time
        if self.end_time:
            return self.end_time - self.start_time
        return 0.0

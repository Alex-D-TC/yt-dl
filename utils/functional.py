class Error:

    def __init__(self, state):
        self.state = state
        self.err_state = False
        self.err = None

    def process(self, func):

        if self.err_state:
            return self

        try:
            self.state = func(self.state)
        except BaseException as e:
            self.err = e
            self.err_state = True

        return self

    def join(self, monad_b, joiner):
        self.state = joiner(self.state, monad_b.state)
        return self

    def consume(self, consumer):
        if not self.err_state:
            consumer(self.state)

    def error(self, handler):
        if self.err_state:
            handler(self.err)

    def extract_state(self):
        return self.state

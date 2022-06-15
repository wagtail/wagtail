from functools import wraps


class disconnect_signal_receiver:
    """
    A decorator that disconnects a signal's receiver during the
    execution of a test and reconnects it back at its end.
    """

    def __init__(self, signal, receiver):
        self.signal = signal
        self.receiver = receiver

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            exception = None
            self.signal.disconnect(self.receiver)

            try:
                func(*args, **kwargs)
            except Exception as e:
                exception = e
            finally:
                self.signal.connect(self.receiver)

            if exception:
                raise exception

        return wrapper

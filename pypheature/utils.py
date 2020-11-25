def compose(*decs):

    def wrapped(func):
        for dec in reversed(decs):
            func = dec(func)
        return func

    return wrapped

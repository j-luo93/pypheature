def compose(*decs):

    def wrapped(func):
        for dec in reversed(decs):
            func = dec(func)
        return func

    return wrapped


def gen_dunder(dunder_name):

    def wrapped(self, *args, **kwargs):
        dunder = getattr(self.wrapped, dunder_name)
        return dunder(*args, **kwargs)

    return wrapped


class temp:
    """A descriptor for a temporary method which gets deleted after class definition."""

    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __getattribute__(self, attr):
        try:
            return super().__getattribute__(attr)
        except AttributeError:
            wrapped = self.wrapped
            return getattr(wrapped, attr)

    __call__ = gen_dunder('__call__')

    def __set_name__(self, owner, name):
        setattr(owner, name, self.wrapped)
        RemoveableMethodMetaclass.add_temp_var_name(name)


class RemoveableMethodMetaclass(type):

    __temp_var_names = list()

    def __init__(cls, *args, **kwargs):
        for name in RemoveableMethodMetaclass.__temp_var_names:
            delattr(cls, name)
        RemoveableMethodMetaclass.__temp_var_names.clear()

        super().__init__(*args, **kwargs)

    @staticmethod
    def add_temp_var_name(name):
        RemoveableMethodMetaclass.__temp_var_names.append(name)


class RemoveableMethod(metaclass=RemoveableMethodMetaclass):
    pass

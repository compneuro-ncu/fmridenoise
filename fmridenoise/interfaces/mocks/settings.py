class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class MockSettings(dict, metaclass=Singleton):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)



if __name__ == '__main__':
    a = MockSettings(test=1, dupa=2)
    print(a)
    a["cos"] = 0
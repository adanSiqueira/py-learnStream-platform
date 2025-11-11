# Helper: fake result object mimicking SQLAlchemy Result with scalars().first()
class FakeResult:
    def __init__(self, first_value):
        self._first = first_value

    def scalars(self):
        # Return an object that has .first()
        class ScalarContainer:
            def __init__(self, value):
                self._value = value

            def first(self):
                return self._value

        return ScalarContainer(self._first)
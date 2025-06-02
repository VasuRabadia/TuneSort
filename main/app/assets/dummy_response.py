class DummyResponse:
    def __init__(self, text="{}"):
        # text should be a stringified dict or list matching expected playlist format
        self.candidates = [self._Candidate(text)]

    class _Candidate:
        def __init__(self, text):
            self.content = self._Content(text)

        class _Content:
            def __init__(self, text):
                self.parts = [self._Part(text)]

            class _Part:
                def __init__(self, text):
                    self.text = text

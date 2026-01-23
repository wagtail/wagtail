class APIAction:
    serializer = None

    def __init__(self, view, request):
        self.view = view
        self.request = request

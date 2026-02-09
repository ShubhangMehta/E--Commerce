class ProductBaseService:
    model = None

    def get_queryset(self):
        return self.model.objects.all()
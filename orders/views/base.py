class OrderBaseView:
    def is_tenant(self, request):
        return request.user.is_staff

class CustomerService:
    def update_profile(self, profile, phone):
        profile.phone = phone
        profile.save()
        return profile

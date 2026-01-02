from django.db import transaction
from users.models import CustomerAddress


class CustomerAddressService:

    @staticmethod
    def add_address(user, data):
        """
        Add a new address.
        - If it's the first address → automatically default + address_type='home'
        - Otherwise, allow custom address type (work/office/other)
        """

        with transaction.atomic():

            user_has_addresses = CustomerAddress.objects.filter(user=user).exists()

            # FIRST address → default home address
            if not user_has_addresses:
                is_default = True
                address_type = "home"   # force home for the first address
            else:
                is_default = data.get("is_default", False)
                address_type = data.get("address_type", "other")  # if not given → other

            address = CustomerAddress.objects.create(
                user=user,
                full_name=data.get("full_name"),
                phone=data.get("phone"),
                house_no=data.get("house_no"),
                landmark=data.get("landmark"),
                city=data.get("city"),
                state=data.get("state"),
                postal_code=data.get("postal_code"),
                address_type=address_type,
                is_default=is_default,
            )

            # If user sets this as default → remove default from all others
            if address.is_default:
                CustomerAddress.objects.filter(user=user).exclude(id=address.id).update(is_default=False)

            return address

    @staticmethod
    def update_address(address, data):
        """
        Update address fields.
        If address is marked as default, unset default for all others.
        """

        with transaction.atomic():

            for attr, value in data.items():
                setattr(address, attr, value)

            address.save()

            # Handle default logic
            if data.get("is_default") is True:
                CustomerAddress.objects.filter(user=address.user).exclude(id=address.id).update(is_default=False)

            return address

    @staticmethod
    def delete_address(address):
        """
        Delete the address.
        If it's the default address → automatically assign another address as default.
        """

        user = address.user
        was_default = address.is_default

        address.delete()

        if was_default:
            # Pick the oldest address as new default
            new_default = CustomerAddress.objects.filter(user=user).first()
            if new_default:
                new_default.is_default = True
                new_default.save()

        return True

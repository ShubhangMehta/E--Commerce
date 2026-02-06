from django.db import transaction
from users.models import Coordinate


class AddressService:

    @staticmethod
    def add_address(subject_member, data):
        with transaction.atomic():

            has_addresses = Coordinate.objects.filter(
                user=subject_member
            ).exists()

            if not has_addresses:
                is_default = True
                address_type = "home"
            else:
                is_default = data.get("is_default", False)
                address_type = data.get("address_type", "other")

            address = Coordinate.objects.create(
                user=subject_member,
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

            if address.is_default:
                Coordinate.objects.filter(
                    user=subject_member
                ).exclude(id=address.id).update(is_default=False)

            return address

    @staticmethod
    def update_address(address, data):
        with transaction.atomic():

            for attr, value in data.items():
                setattr(address, attr, value)

            address.save()

            if data.get("is_default") is True:
                Coordinate.objects.filter(
                    user=address.user
                ).exclude(id=address.id).update(is_default=False)

            return address

    @staticmethod
    def delete_address(address):
        subject_member = address.user
        was_default = address.is_default

        address.delete()

        if was_default:
            new_default = Coordinate.objects.filter(
                user=subject_member
            ).first()

            if new_default:
                new_default.is_default = True
                new_default.save()

        return True

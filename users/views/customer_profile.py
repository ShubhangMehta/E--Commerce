from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from users.serializers import SubjectMemberSerializer
from users.services.customer_profile_service import ProfileService
from users.models import SubjectMember


def get_subject_member(request):
    return SubjectMember.objects.get(
        global_user_id=request.user.id,
        is_active=True
    )


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subject_member = get_subject_member(request)

        # Serialize model instance directly
        serializer = SubjectMemberSerializer(subject_member)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        subject_member = get_subject_member(request)
        ProfileService.update_profile(subject_member, request.data)

        return Response(
            {"message": "Profile updated"},
            status=status.HTTP_200_OK
        )

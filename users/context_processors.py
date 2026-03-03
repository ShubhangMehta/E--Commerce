from .models import SubjectMember

def owner_status(request):
    is_owner = False

    if request.user.is_authenticated:
        member = SubjectMember.objects.filter(
            global_user_id=request.user.id
        ).first()

        if member and member.role.strip().upper() == "OWNER":
            is_owner = True

    return {
        "is_owner": is_owner
    }
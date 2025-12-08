from django.shortcuts import render

# Create your views here.
def index(request):
    theme = request.tenant.theme
    return render(request, f"themes/{theme}/index.html")

def theme_settings(request):
    selected_theme = request.GET.get("theme")

    if selected_theme:
        tenant = request.tenant
        tenant.theme = selected_theme
        tenant.save()

    return render(request, "dashboard/themes.html")


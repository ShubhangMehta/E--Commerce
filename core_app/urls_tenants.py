from django.urls import path, include
# from themes import views as themes_views
# from dashboard import views as dashboard_views



urlpatterns = [
    # path("", themes_views.index, name="themes_home"),

    path('', include('themes.urls')),
    path('', include('dashboard.urls')),   
]
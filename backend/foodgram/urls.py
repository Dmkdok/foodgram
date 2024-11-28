from django.contrib import admin
from django.urls import include, path

from api.views import RecipeViewSet

urlpatterns = [
    path(
        's/<int:pk>/',
        RecipeViewSet.as_view({'get': 'redirect_to_short_link'}),
        name='short_link_redirect',
    ),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]

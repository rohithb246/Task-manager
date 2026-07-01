from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
<<<<<<< HEAD
from django.views.decorators.cache import never_cache
=======
>>>>>>> 2a7d8f410b51eeac078385d3560f6cde3e29435b
from django.views.generic import TemplateView


urlpatterns = [
<<<<<<< HEAD
    path("", never_cache(TemplateView.as_view(template_name="index.html")), name="home"),
=======
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
>>>>>>> 2a7d8f410b51eeac078385d3560f6cde3e29435b
    path('admin/', admin.site.urls),
    path('api/', include('tasks.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

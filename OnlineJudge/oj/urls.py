from django.conf.urls import include, url
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    url(r"^api/", include("account.urls.oj")),
    url(r"^api/", include("announcement.urls.oj")),
    url(r"^api/admin/", include("announcement.urls.admin")),
    url(r"^api/", include("conf.urls.oj")),
    url(r"^api/admin/", include("conf.urls.admin")),
    url(r"^api/", include("problem.urls.oj")),
    url(r"^api/admin/", include("problem.urls.admin")),
    url(r"^api/", include("contest.urls.oj")),
    url(r"^api/admin/", include("contest.urls.admin")),
    url(r"^api/", include("submission.urls.oj")),
    url(r"^api/admin/", include("submission.urls.admin")),
    url(r"^api/admin/", include("utils.urls")),
    url(r"^api/admin/", include("account.urls.admin")),
    url(r"^api/", include("ai.urls")),
    path('api/admin/', include('assignment.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
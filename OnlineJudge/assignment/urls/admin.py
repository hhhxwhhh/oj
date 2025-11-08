from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from ..views import AssignmentViewSet, StudentAssignmentViewSet

# 管理员路由
router = DefaultRouter()
router.register(r'student-assignments', StudentAssignmentViewSet, basename='student-assignment')
router.register(r'', AssignmentViewSet, basename='assignment')

urlpatterns = [
    url(r'^', include(router.urls)),
]
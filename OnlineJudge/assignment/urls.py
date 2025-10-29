from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssignmentViewSet, StudentAssignmentViewSet

router = DefaultRouter()
router.register(r'assignments', AssignmentViewSet, basename='assignment')
router.register(r'student-assignments', StudentAssignmentViewSet, basename='student-assignment')

urlpatterns = [
    path('', include(router.urls)),
]
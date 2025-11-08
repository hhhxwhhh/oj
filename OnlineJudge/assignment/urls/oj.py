from django.conf.urls import url
from ..views import UserAssignmentsAPI, StudentAssignmentDetailAPI, StudentAssignmentProgressAPI

urlpatterns = [
    # 获取当前用户的所有作业
    url(r'^user-assignments/?$', UserAssignmentsAPI.as_view(), name="user_assignment_list_api"),
    
    # 获取单个学生作业详情
    url(r'^student-assignments/(?P<pk>[0-9]+)/?$', StudentAssignmentDetailAPI.as_view(), name="student_assignment_detail"),
    
    # 获取学生作业进度
    url(r'^student-assignments/(?P<pk>[0-9]+)/progress/?$', StudentAssignmentProgressAPI.as_view(), name="student_assignment_progress"),
]
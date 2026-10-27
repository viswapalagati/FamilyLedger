from django.urls import path

from . import views

app_name = "families"

urlpatterns = [
    path("members/", views.MemberListView.as_view(), name="member_list"),
    path("members/add/", views.MemberCreateView.as_view(), name="member_add"),
    path("members/<int:pk>/", views.MemberDetailView.as_view(), name="member_detail"),
    path("members/<int:pk>/edit/", views.MemberUpdateView.as_view(), name="member_edit"),
    path("members/<int:pk>/manage/", views.ManageMemberView.as_view(), name="member_manage"),
    path("members/<int:pk>/create-login/", views.CreateLoginView.as_view(), name="member_create_login"),
    path("members/<int:pk>/deactivate/", views.MemberDeactivateView.as_view(), name="member_deactivate"),
    path("settings/", views.FamilySettingsView.as_view(), name="settings"),
]

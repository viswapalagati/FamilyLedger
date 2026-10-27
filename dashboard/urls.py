from django.urls import path

from . import views

app_name = "dashboard"

print("dashboard urls.py loaded")
urlpatterns = [
    path("", views.OverviewView.as_view(), name="overview"), #Base_url/dashboard/
    path("family/", views.FamilyReportView.as_view(), name="family"),
    path("member/<int:pk>/", views.MemberReportView.as_view(), name="member"),
    path("category/<int:pk>/", views.CategoryDrillView.as_view(), name="category"),
    path("api/chart/<slug:slug>/", views.ChartDataView.as_view(), name="chart_data"),
]

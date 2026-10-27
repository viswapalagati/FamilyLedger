from django.urls import path

from . import views

app_name = "assets"

urlpatterns = [
    path("net-worth/", views.NetWorthView.as_view(), name="networth"),

    path("bank/", views.BankListView.as_view(), name="bank_list"),
    path("bank/add/", views.BankCreateView.as_view(), name="bank_add"),
    path("bank/<int:pk>/edit/", views.BankUpdateView.as_view(), name="bank_edit"),
    path("bank/<int:pk>/delete/", views.BankDeleteView.as_view(), name="bank_delete"),

    path("physical/", views.PhysicalListView.as_view(), name="physical_list"),
    path("physical/add/", views.PhysicalCreateView.as_view(), name="physical_add"),
    path("physical/<int:pk>/edit/", views.PhysicalUpdateView.as_view(), name="physical_edit"),
    path("physical/<int:pk>/delete/", views.PhysicalDeleteView.as_view(), name="physical_delete"),

    path("digital/", views.DigitalListView.as_view(), name="digital_list"),
    path("digital/add/", views.DigitalCreateView.as_view(), name="digital_add"),
    path("digital/<int:pk>/edit/", views.DigitalUpdateView.as_view(), name="digital_edit"),
    path("digital/<int:pk>/delete/", views.DigitalDeleteView.as_view(), name="digital_delete"),

    path("other/", views.OtherListView.as_view(), name="other_list"),
    path("other/add/", views.OtherCreateView.as_view(), name="other_add"),
    path("other/<int:pk>/edit/", views.OtherUpdateView.as_view(), name="other_edit"),
    path("other/<int:pk>/delete/", views.OtherDeleteView.as_view(), name="other_delete"),
]

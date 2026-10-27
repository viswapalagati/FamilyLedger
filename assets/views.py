"""assets views — SKELETON. Implement per §4.6-§4.9, §4.12 (FR-12.5), §6, §14.2.

Four near-identical CRUD sets (bank | physical | digital | other) plus the net
worth page. Build shared private bases and subclass them per kind.

Routes (assets/urls.py, already wired):
  net-worth/                         NetWorthView
  <kind>/  <kind>/add/  <kind>/<pk>/edit/  <kind>/<pk>/delete/
      -> {Bank,Physical,Digital,Other}{List,Create,Update,Delete}View

Templates: assets/asset_list.html, core/object_form.html,
core/object_confirm_delete.html, assets/networth.html.
The list template reads: list_title, add_url_name, edit_url_name,
delete_url_name, kind_key, members, selected_owner, items, net_total.
"""

from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from core.mixins import (  # noqa: F401
    FamilyFormKwargsMixin,
    FamilyRequiredMixin,
    FamilyScopedQuerysetMixin,
    RecordEditPermissionMixin,
)

from django.contrib import messages 

from .models import BankAccount, DigitalAsset, PhysicalAsset, OtherFinancialInfo
from .forms import BankAccountForm, PhysicalAssetForm, DigitalAssetForm, OtherFinancialInfoForm
from django.urls import reverse_lazy
from dashboard.services import net_worth


class _AssetListView(FamilyRequiredMixin, FamilyScopedQuerysetMixin, ListView):
    template_name = "assets/asset_list.html"
    context_object_name = "items"
    list_title = "Assets"
    add_url_name = ""
    kind_key = ""
    # TODO: owner filter; context (see module docstring); net_total = sum of
    #       item.net_worth_value.
    def get_queryset(self):
        qs = super().get_queryset().select_related("owner", "registered_by")
        owner = self.request.GET.get("owner")
        if owner:
            qs = qs.filter(owner_id=owner)
        return qs 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_title"] = self.list_title
        context["add_url_name"] = self.add_url_name
        context["edit_url_name"] = self.add_url_name.replace("_add", "_edit")
        context["delete_url_name"] = self.add_url_name.replace("_add", "_delete")
        context["kind_key"] = self.kind_key
        context["members"] = self.family.active_members
        context["selected_owner"] = self.request.GET.get("owner" ,"")
        total = sum((i.net_worth_value for i in context["items"]), 0)
        context["net_total"] = total
        return context

    



class _AssetCreateView(FamilyRequiredMixin, FamilyFormKwargsMixin, CreateView):
    template_name = "core/object_form.html"
    form_title = "New asset"
    # TODO: object_form context keys; success message.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = self.form_title 
        context["submit_lable"] = "Save"
        context["cancel_url"] = self.success_url
        return context 

    def form_valid(self, form):
        messages.success(self.request, f"{self.form_title} saved.")
        return super().form_valid(form)



class _AssetUpdateView(FamilyRequiredMixin, FamilyScopedQuerysetMixin,
                       FamilyFormKwargsMixin, RecordEditPermissionMixin, UpdateView):
    template_name = "core/object_form.html"
    form_title = "Edit asset"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_valid"] = self.form_valid
        context["submit_label"] = "Save"
        context["cancel_url"] = self.success_url
        return context 


class _AssetDeleteView(FamilyRequiredMixin, FamilyScopedQuerysetMixin,
                       RecordEditPermissionMixin, DeleteView):
    template_name = "core/object_confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Deleted.")
        return self.success_url 


# ---- bank ---------------------------------------------------------------- #
class BankListView(_AssetListView):
    model = BankAccount
    list_title = "Bank accounts"
    add_url_name = "assets:bank_add"
    kind_key = "bank"


class BankCreateView(_AssetCreateView):
    model = BankAccount
    form_class = BankAccountForm
    success_url = reverse_lazy("assets:bank_list")
    list_title = "New Bank Account"


class BankUpdateView(_AssetUpdateView):
    model = BankAccount
    form_class = BankAccountForm
    success_url = reverse_lazy("assets:bank_list")
    list_title = "Edit Bank Account"


class BankDeleteView(_AssetDeleteView):
    model = BankAccount
    success_url = reverse_lazy("assets:bank_list")


# ---- physical --------------------------------------------------------- #
class PhysicalListView(_AssetListView):
    model = PhysicalAsset
    list_title = "Physical assets"
    add_url_name = "assets:physical_add"
    kind_key = "physical"


class PhysicalCreateView(_AssetCreateView):
    model = PhysicalAsset
    form_class = PhysicalAssetForm
    success_url = reverse_lazy("assets:physical_list")
    form_title = "New physical asset"


class PhysicalUpdateView(_AssetUpdateView):
    model = PhysicalAsset
    form_class = PhysicalAssetForm
    success_url = reverse_lazy("assets:physical_list")


class PhysicalDeleteView(_AssetDeleteView):
    model = PhysicalAsset
    success_url = reverse_lazy("assets:physical_list")



# ---- digital -------------------------------------------------------- #
class DigitalListView(_AssetListView):
    model = DigitalAsset
    list_title = "Digital assets"
    add_url_name = "assets:digital_add"
    kind_key = "digital"


class DigitalCreateView(_AssetCreateView):
    model = DigitalAsset
    form_class = DigitalAssetForm
    success_url = reverse_lazy("assets:digital_list")
    form_title = "New digital asset"


class DigitalUpdateView(_AssetUpdateView):
    model = DigitalAsset
    form_class = DigitalAssetForm
    success_url = reverse_lazy("assets:digital_list")
    form_title = "Edit digital asset"


class DigitalDeleteView(_AssetDeleteView):
    model = DigitalAsset
    success_url = reverse_lazy("assets:digital_list")


# ---- other -------------------------------------------------------- #
class OtherListView(_AssetListView):
    model = OtherFinancialInfo
    list_title = "Other financial info"
    add_url_name = "assets:other_add"
    kind_key = "other"


class OtherCreateView(_AssetCreateView):
    model = OtherFinancialInfo
    form_class = OtherFinancialInfoForm
    success_url = reverse_lazy("assets:other_list")
    form_title = "New financial record"


class OtherUpdateView(_AssetUpdateView):
    model = OtherFinancialInfo
    form_class = OtherFinancialInfoForm
    success_url = reverse_lazy("assets:other_list")
    form_title = "Edit financial record"


class OtherDeleteView(_AssetDeleteView):
    model = OtherFinancialInfo 
    success_url = reverse_lazy("assets:other_list")


# ---- net worth (FR-12.5, BR-11) --------------------------------- #
class NetWorthView(FamilyRequiredMixin, TemplateView):
    """Template: assets/networth.html. Context: family_nw, member_rows
    (each {member, nw}), sorted by nw['total'] desc. Use dashboard.services.net_worth."""

    template_name = "assets/networth.html"
    # TODO: implement get_context_data()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["family_nw"] = net_worth(self.family)
        rows = []
        for member in self.family.active_members:
            rows.append({"member":member, "nw":net_worth(self.family, member)})
        rows.sort(key=lambda r: r["nw"] ["total"], reverse=True)
        context["member_rows"] = rows 
        return context 
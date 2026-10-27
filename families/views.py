"""families views — SKELETON. Implement per §4.2 (FR-2.*), §6 (permissions),
§14.2 (screens) and §15 (forms).

Routes (families/urls.py, already wired):
  members/                       MemberListView
  members/add/                   MemberCreateView
  members/<pk>/                   MemberDetailView
  members/<pk>/edit/             MemberUpdateView      (added_by / self / admin)
  members/<pk>/manage/           ManageMemberView      (admin)
  members/<pk>/create-login/     CreateLoginView       (added_by / admin)
  members/<pk>/deactivate/       MemberDeactivateView  (admin, not self)
  settings/                      FamilySettingsView    (admin)
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import (
    DetailView,
    FormView,
    ListView,
    UpdateView,
)

from core.mixins import FamilyAdminRequiredMixin, FamilyRequiredMixin
from families.emails import send_account_created_email
from families.forms import AddMemberForm, MemberEditForm, ManageMemberForm, CreateLoginForm, FamilySettingsForm
from ledger.models import Transaction, TxnType
from django.db.models import Sum 
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from .models import FamilyMember


class MemberListView(FamilyRequiredMixin, ListView):
    """All members of the family (FR-2.5). Template: families/member_list.html."""

    template_name = "families/member_list.html"
    context_object_name = "members"
    # TODO: get_queryset() -> self.family.members ...
    def get_queryset(self):
            return self.family.members.select_related("user", "added_by").all()



class MemberDetailView(FamilyRequiredMixin, DetailView):
    """One member + lifetime totals + recent txns + action gates (FR-2.6)."""

    template_name = "families/member_detail.html"
    context_object_name = "member"
    # TODO: family-scoped queryset; context: income_total, expense_total, recent,
    #       can_manage, can_edit.
    def get_queryset(self):
        return self.family.members.select_related("user", "added_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = self.get_object()
        totals = (Transaction.objects.filter(member=member).values("txn_type")
            .annotate(total=Sum("amount")))
        by_type = {row["txn_type"]: row["total"] or 0 for row in totals}
        context["income_total"] = by_type.get(TxnType.INCOME, 0)
        context["expense_total"] = by_type.get(TxnType.EXPENSE, 0)
        context["revcet"] = (Transaction.objects.filter(member=member).select_related("account_head", "recorded_by")[:10])
        context["can_manage"] = self.acting_member.is_family_admin
        context["can_edit"] = (
            self.acting_member.is_family_admin 
            or member.added_by_id == self.acting_member.pk
            or member.pk == self.acting_member.pk)

        return context




class MemberCreateView(FamilyRequiredMixin, FormView):
    """Add-member flow (FR-2.1-2.4). Template: families/member_form.html.

    Pass family + added_by to AddMemberForm; on success send the account-created
    email when a login was made (FR-13), then redirect to the member detail page.
    """

    template_name = "families/member_form.html"
    form_class = AddMemberForm  # TODO: implement form; pass family + added_by; save() must be atomic

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["family"] = self.family
        kwargs["added_by"] = self.acting_member
        return kwargs

    def form_valid(self, form):
        member = form.save()
        if member.has_login:
            try:
                send_account_created_email(member, self.acting_member)
                messages.success(
                    self.request,
                    f"{member.full_name} was added successfully and email was sent.",
                )
            except Exception:
                messages.warning(
                    self.request,
                    f"{member.full_name} was added successfully but email could not be sent.",
                )

        else:
            messages.success(
                self.request, f"{member.full_name} was added (no login)."
            )

        return redirect("families:member_detail", pk=member.pk)
    





class MemberUpdateView(FamilyRequiredMixin, UpdateView):
    """Edit member details (FR-2.7). Permission: added_by / self / admin."""

    template_name = "core/object_form.html"
    form_class = MemberEditForm
    # TODO: form_class = MemberEditForm; permission check in get_object();
    #       object_form context + success_url (member detail).
    
    def get_queryset(self):
        return self.family.members.all()

    def get_object_data(self, queryset=None):
        obj = super().get_object(queryset)
        if not (
            self.acting_member.is_family_admin
            or obj.added_by_id == self.acting_member.pk 
            or obj.pk == self.acting_member.pk
        ):
            raise self.PermissionDenied("You cannot edit this details")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["family_title"] = f"Edit{self.object.full_name}"
        context["submt_lable"] = "Save member"
        context["clean_url"] = reverse("families:member_detail", args=[self.object.pk])
        return context

    def get_success_url(self):
        return reverse("families:member_detail", args= [self.object.pk])
        

class ManageMemberView(FamilyAdminRequiredMixin, UpdateView):
    """Admin-only role/status (FR-2.9, BR-16 — not self)."""

    template_name = "core/object_form.html"
    # TODO: form_class = ManageMemberForm; block self; success_url.
    form_class = ManageMemberForm
    def get_queryset(self):
        return self.family.members.all()

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.pk == self.acting_member.pk:
            raise PermissionDenied("You cannot change your own role or status here")
        return obj 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = f"Manage {self.object.full_name}"
        context["form_help"] = (
            "Member with financial history are deactivated, never deleted"
        )
        context["submit_label"] = "Apply"
        context["cancel_url"] = reverse("families:member_detail", args=[self.object.pk])
        return context 

    def get_success_url(self):
        messages.success(self.request, f"Updated {self.object.full_name}.")
        return reverse("families:member_detail", args=[self.object.pk])

    

class CreateLoginView(FamilyRequiredMixin, FormView):
    """Give a login-less member a login (FR-2.8). Template: families/create_login.html."""

    template_name = "families/create_login.html"
    form_class = CreateLoginForm
    # TODO: resolve member; permission (admin or added_by); member must not have a
    #       login; pass member to CreateLoginForm; send email; redirect to detail.

    def dispatch(self, request, *args, **kwargs):
        response_or_none = super().dispatch(request, *args, **kwargs)
        return response_or_none 

    def get_member(self):
        member = get_object_or_404(self.family.members, pk=self.kwargs["pk"])
        if member.has_login:
            raise PermissionDenied("This member already has login")
        if not (
            self.acting_member.is_family_admin 
            or member.added_by_id == self.acting_member.pk
        ):
            raise PermissionDenied("Only an admin or the person who added them can do this.")
        return member

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["member"] = self.get_member()
        return kwargs

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context["member"] = self.get_member()
        return context 

    def form_valid(self, form):
        member = form.save()
        try:
            send_account_created_email(member, self.acting_member)
        except Exception:
            messages.warning(self.request, "Login created, but the email could not be sent.")
        messages.success(self.request, f"Login creted for {member.full_name}.")
        return redirect("families:member_detail", pk=member.pk)



class MemberDeactivateView(FamilyAdminRequiredMixin, UpdateView):
    """Deactivate a member (FR-2.10, BR-8). Template: core/object_confirm_delete.html."""

    fields = []
    template_name = "core/object_confirm_delete.html"

    def get_queryset(self):
        return self.family.members.all()

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.pk == self.acting_member.pk:
            raise PermissionDenied("You cannot deactivate yourself.")
        return obj

    def form_valid(self, form):
        self.object.status = FamilyMember.Status.INACTIVE
        if self.object.user_id:
            self.object.user.is_active = False
            self.object.user.save(update_fields=["is_active"])
        self.object.save(update_fields=["status", "updated_at"])
        messages.success(self.request, f"{self.object.full_name} was deactivated.")
        return redirect("families:member_detail", pk=self.object.pk)
        



class FamilySettingsView(FamilyAdminRequiredMixin, UpdateView):
    """Family name + FY start month (FR-2.12). Template: core/object_form.html."""

    template_name = "core/object_form.html"
    # TODO: form_class = FamilySettingsForm; get_object() -> self.family; success_url.
    form_class = FamilySettingsForm
    success_url = reverse_lazy("families:settings")

    def get_object(self, queryset = None):
        return self.family

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Family settings"
        context["submit label"] = "Save settings"
        context["cancel_url"] = reverse("dashboard:overview")
        return context 

    def form_valid(self, form):
        messages.success(self.request, "Family settings updated.")
        return super().form_valid(form)        
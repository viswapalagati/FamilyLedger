"""Reusable class-based-view mixins — SKELETON.

Implement per the FamilyLedger Build Specification:
  §6  Authorization Model
  §11 Reusable CBV Mixins   (behaviour of each class is specified there)
  BR-2 (family isolation -> 404), BR-5 (record edit rights)

Every view in the project composes these. Nothing here is implemented yet.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin  # noqa: F401
from django.core.exceptions import PermissionDenied  # noqa: F401
from django.shortcuts import redirect
from datetime import date, datetime  # noqa: F401
from core.periods import PERIOD_CHOICES, resolve_period  # noqa: F401
from families.models import FamilyMember  # noqa: F401


class FamilyRequiredMixin(LoginRequiredMixin):
    """Require an authenticated user backed by an *active* FamilyMember.

    On success expose ``self.acting_member`` and ``self.family`` and add both to
    the template context. Raise ``PermissionDenied`` when the login has no member
    record or the member's status is not ``active`` (§11.1, FR-2.11, FR-3.4).
    An unlinked superuser is redirected to Django admin to set up a family.
    """
    print("FamilyRequiredMixin loaded")
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        print("dispatching FamilyRequiredMixin")

        member = request.user.family_member_or_none
        print("dispatching FamilyRequiredMixin", member)
        if member is None:
            if request.user.is_superuser:
                messages.warning(
                    request,
                    "This superuser is not linked to a family. In Django admin, "
                    "create a Family and an active FamilyMember linked to this account.",
                )
                return redirect("admin:index")
            raise PermissionDenied("Your login is not linked to a family member.")
        if member.status != member.Status.ACTIVE:
            raise PermissionDenied("Your family membership is inactive.")

        self.acting_member = member
        self.family = member.family
        print("dispatching FamilyRequiredMixin", self.acting_member, self.family)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["acting_member"] = getattr(self, "acting_member", None)
        context["family"] = getattr(self, "family", None)
        print("FamilyRequiredMixin context data prepared", context)
        return context


class FamilyScopedQuerysetMixin:
    """Restrict the view's queryset to ``self.family`` (§11.2, BR-2).

    ``get_queryset()`` -> ``super().get_queryset().filter(family=self.family)``.
    This is what turns cross-family object access into HTTP 404.
    """

    # TODO: implement get_queryset()
    def get_queryset(self):
        return super().get_queryset().filter(family=self.family)


class FamilyFormKwargsMixin:
    """Pass ``family`` and ``acting_member`` into the form (§11.3, §15.1)."""

    # TODO: implement get_form_kwargs()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["family"] = self.family
        kwargs["acting_member"] = self.acting_member
        return kwargs   

    

    



class FamilyAdminRequiredMixin(FamilyRequiredMixin):
    """Family-admin-only views (§11.4, §6.1). Raise PermissionDenied otherwise."""

    # TODO: gate get()/post() on self.acting_member.is_family_admin
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        return response

    def get(self, request, *args, **kwargs):
        self._require_admin()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._require_admin()
        return super().post(request, *args, **kwargs)

    def _require_admin(self):
        if not self.acting_member.is_family_admin:
            raise PermissionDenied("This action is restricted to family admins.")



class RecordEditPermissionMixin:
    """Guard edit/delete to owner / recorder / family admin (§11.5, BR-5).

    Wrap ``get_object()``; call ``obj.editable_by(self.acting_member)``.
    """

    # TODO: implement get_object()
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        checker = getattr(obj, "editable_by", None)
        allowed = checker(self.acting_member) if callable(checker) else True
        if not allowed and not self.acting_member.is_family_admin:
            raise PermissionDenied("You cannot modify this record.")
        return obj


class ScopePeriodMixin(FamilyRequiredMixin):
    """Resolve ``?scope`` / ``?period`` / ``?anchor`` for report & list views.

    Specified in full in §11.6 and §4.11 (FR-11.*). Provides:
      self.scope            -- "me" | "member:<pk>" | "family"  (normalised)
      self.scope_member     -- FamilyMember or None (family scope)
      self.period           -- result of core.periods.resolve_period(...)
      self.anchor_date      -- date
      scope_transactions(qs)   -- family + member + period filtered queryset
      scope_choices()          -- [(value, label), ...] for the selector
      get_filter_ctx(extra=)   -- dict consumed by core/_scope_period.html
    """

    default_scope = "me"
    default_period = "month"

    # TODO: implement _prepare_scope_period(), get(), scope_transactions(),
    #       scope_choices(), get_filter_ctx()
    print("ScopePeriodMixin loaded")
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_filter_ctx())
        print("ScopePeriodMixin context data prepared", context)
        return context

    def get_filter_ctx(self, extra=None):
        """Return a dict suitable for the template's filter context.

        extra: list of (label, value) tuples to append to the period selector.
        """
        print("get_filter_ctx called")
        if extra is None:
            extra = []
        return {
            "period_label": self.period.label,
            "scope_choices": self.scope_choices(),
            "scope": self.scope,
            "period_choices": PERIOD_CHOICES,
            "period": self.period.period_type,
            "anchor": self.anchor_date.isoformat(),
            "extra": extra,
        }

    def scope_transactions(self, qs):
        """Return a queryset filtered to the current scope and period.

        qs: a family-scoped queryset (e.g. Transaction.objects.filter(family=self.family))
        """
        print("scope_transactions called") 
        #qs = qs.filter(date__gte=self.period.start, date__lte=self.period.end)
        qs = qs.in_period(self.period)
        if self.scope == "me":
            qs = qs.filter(recorded_by=self.acting_member)
        elif self.scope.startswith("member:"):
            qs = qs.filter(recorded_by=self.scope_member)
        return qs

    def scope_choices(self):
        """Return a list of (value, label) tuples for the scope selector.

        Includes "me" and "family" plus all active family members.
        """
        print("scope_choices called")
        choices = [("me", "My transactions")]
        print("Scope choices before loop:", choices)
        for member in self.family.members.filter(status=FamilyMember.Status.ACTIVE):
            print("For loop in scope_choices", member)
            choices.append((f"member:{member.pk}", member.full_name))
        print("Scope choices before append:", choices)
        choices.append(("family", "All family transactions"))
        print("Scope choices after loop:", choices)
        return choices

    def _prepare_scope_period(self):
        """Resolve self.scope, self.scope_member, self.period, self.anchor_date.
        Called by get() before rendering the view. Raises PermissionDenied if the
        requested scope is not allowed for the acting_member.
        """
        # Resolve scope
        print("Preparing scope and period loaded")
        self.scope = self.request.GET.get("scope", self.default_scope)
        print("Scope:", self.scope)
        if self.scope == "me":
            self.scope_member = self.acting_member
            print("Scope member set to acting member",self.scope_member)
        elif self.scope.startswith("member:"):
            member_id = int(self.scope.split(":")[1])
            try:
                self.scope_member = self.family.members.get(pk=member_id)
            except FamilyMember.DoesNotExist:
                raise PermissionDenied("You do not have permission to view this member's transactions.")
        elif self.scope == "family":
            self.scope_member = None
        else:
            raise PermissionDenied("Invalid scope parameter.")

        # Resolve period and anchor date
        period_name = self.request.GET.get("period", self.default_period)
        print("Period name:", period_name)
        anchor_str = self.request.GET.get("anchor", None)
        print("Anchor string:", anchor_str)
        if anchor_str:
            try:
                anchor_date = datetime.strptime(anchor_str, "%Y-%m-%d").date()
            except ValueError:
                raise PermissionDenied("Invalid anchor date format.")
        else:
            anchor_date = date.today()

        self.period = resolve_period(period_name, anchor_date)
        print("Resolved period:", self.period)
        self.anchor_date = anchor_date 
        print("Anchor date:", self.anchor_date) 

    def get(self, request, *args, **kwargs):
        self._prepare_scope_period()
        print("scope periodmixin get function called")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self._prepare_scope_period()
        print("scope periodmixin post function called")
        return super().post(request, *args, **kwargs)

        
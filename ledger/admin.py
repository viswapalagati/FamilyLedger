"""ledger admin — SKELETON (FR-14.1).

Register AccountHead, Transaction, RecurringTemplate with useful list_display /
list_filter / search_fields / date_hierarchy / autocomplete_fields. See §14.
Transaction.occurred_date is read-only.
"""

from django.contrib import admin

from .models import AccountHead, RecurringTemplate, Transaction

from .audit import audit_snapshot, record_audit_event
from .models import (
    AccountHead,
    AuditEvent,
    Budget,
    GoalContribution,
    RecurringTemplate,
    SavingsGoal,
    Transaction,
)


class AuditedModelAdmin(admin.ModelAdmin):
    audit_entity_type = None

    def _record_event(self, request, obj, action, before=None):
        actor = getattr(request.user, "family_member_or_none", None)
        if actor and actor.family_id != obj.family_id:
            actor = None
        record_audit_event(
            family=obj.family,
            actor=actor,
            actor_user=request.user,
            action=action,
            entity_type=self.audit_entity_type,
            instance=obj,
            before=before,
        )

    def save_model(self, request, obj, form, change):
        before = None
        if change:
            previous = type(obj).objects.get(pk=obj.pk)
            before = audit_snapshot(previous)
        super().save_model(request, obj, form, change)
        action = AuditEvent.Action.UPDATED if change else AuditEvent.Action.CREATED
        self._record_event(request, obj, action, before)

    def delete_model(self, request, obj):
        self._record_event(
            request,
            obj,
            AuditEvent.Action.DELETED,
            audit_snapshot(obj),
        )
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        objects = list(queryset)
        for obj in objects:
            self._record_event(
                request,
                obj,
                AuditEvent.Action.DELETED,
                audit_snapshot(obj),
            )
        super().delete_queryset(request, queryset)


class AuditedTabularInline(admin.TabularInline):
    audit_entity_type = None

    def _record_event(self, request, obj, action, before=None):
        actor = getattr(request.user, "family_member_or_none", None)
        if actor and actor.family_id != obj.family_id:
            actor = None
        record_audit_event(
            family=obj.family,
            actor=actor,
            actor_user=request.user,
            action=action,
            entity_type=self.audit_entity_type,
            instance=obj,
            before=before,
        )

    def save_model(self, request, obj, form, change):
        before = None
        if change:
            before = audit_snapshot(type(obj).objects.get(pk=obj.pk))
        super().save_model(request, obj, form, change)
        action = AuditEvent.Action.UPDATED if change else AuditEvent.Action.CREATED
        self._record_event(request, obj, action, before)

    def delete_model(self, request, obj):
        self._record_event(
            request,
            obj,
            AuditEvent.Action.DELETED,
            audit_snapshot(obj),
        )
        super().delete_model(request, obj)


@admin.register(AccountHead)
class AccountHeadAdmin(admin.ModelAdmin):
    list_display = ["name", "family", "kind", "parent", "is_archived"]
    list_filter = ["family", "kind", "is_archived"]
    search_fields = ["name"]


@admin.register(Transaction)
class TransactionAdmin(AuditedModelAdmin):
    audit_entity_type = AuditEvent.EntityType.TRANSACTION

    list_display = [
        "occurred_date", "family", "member", "txn_type", "account_head",
        "amount", "merchant_or_source", "recorded_by",
    ]
    list_filter = ["family", "txn_type", "payment_method", "occurred_date"]
    search_fields = ["merchant_or_source", "description"]
    date_hierarchy = "occurred_date"
    autocomplete_fields = ["member", "recorded_by", "account_head", "bank_account"]
    readonly_fields = ["occurred_date"]


@admin.register(RecurringTemplate)
class RecurringTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "family", "member", "txn_type", "amount", "frequency",
        "next_run_date", "is_active",
    ]
    list_filter = ["family", "txn_type", "frequency", "is_active"]


@admin.register(Budget)
class BudgetAdmin(AuditedModelAdmin):
    audit_entity_type = AuditEvent.EntityType.BUDGET

    list_display = ["family", "account_head", "year", "month", "amount", "created_by"]
    list_filter = ["family", "year", "month"]
    autocomplete_fields = ["account_head", "created_by"]


class GoalContributionInline(AuditedTabularInline):
    audit_entity_type = AuditEvent.EntityType.GOAL_CONTRIBUTION
    model = GoalContribution
    extra = 0
    autocomplete_fields = ["member"]


@admin.register(SavingsGoal)
class SavingsGoalAdmin(AuditedModelAdmin):
    audit_entity_type = AuditEvent.EntityType.SAVINGS_GOAL

    list_display = ["name", "family", "target_amount", "target_date", "created_by"]
    list_filter = ["family", "target_date"]
    search_fields = ["name", "description"]
    autocomplete_fields = ["created_by"]
    inlines = [GoalContributionInline]


@admin.register(GoalContribution)
class GoalContributionAdmin(AuditedModelAdmin):
    audit_entity_type = AuditEvent.EntityType.GOAL_CONTRIBUTION
    list_display = ["goal", "family", "member", "amount", "contributed_on"]
    list_filter = ["family", "contributed_on"]
    search_fields = ["goal__name", "member__full_name", "note"]
    autocomplete_fields = ["goal", "member"]


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "family",
        "action",
        "entity_type",
        "entity_id",
        "actor_name",
    ]
    list_filter = ["family", "action", "entity_type", "created_at"]
    search_fields = ["summary", "actor_name", "actor_email", "entity_id"]
    readonly_fields = [
        "family",
        "actor",
        "actor_name",
        "actor_email",
        "action",
        "entity_type",
        "entity_id",
        "summary",
        "changes",
        "created_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
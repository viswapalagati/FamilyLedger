from decimal import Decimal

from .models import (
    AccountHead,
    AuditEvent,
    Budget,
    GoalContribution,
    SavingsGoal,
    Transaction,
)


AUDITED_FIELDS = {
    Transaction: (
        "txn_type",
        "amount",
        "occurred_date",
        "member",
        "recorded_by",
        "account_head",
        "merchant_or_source",
        "description",
        "payment_method",
        "bank_account",
    ),
    Budget: ("account_head", "year", "month", "amount"),
    SavingsGoal: ("name", "description", "target_amount", "target_date"),
    GoalContribution: ("goal", "amount", "contributed_on", "note", "member"),
}


def audit_snapshot(instance):
    fields = AUDITED_FIELDS.get(type(instance))
    if fields is None:
        raise TypeError(f"Unsupported audit record: {type(instance).__name__}")
    snapshot = {}
    for field in fields:
        related_id = getattr(instance, f"{field}_id", None)
        if related_id is not None:
            snapshot[field] = related_id
            related_object = getattr(instance, field, None)
            if field in {"account_head", "goal", "member", "recorded_by"} and related_object:
                snapshot[f"{field}_label"] = str(related_object)
        else:
            value = getattr(instance, field)
            if isinstance(value, Decimal):
                value = str(value)
            elif hasattr(value, "isoformat"):
                value = value.isoformat()
            snapshot[field] = value
    if hasattr(instance, "family_id"):
        snapshot["family_id"] = instance.family_id
    return snapshot


def record_audit_event(
    *,
    family,
    actor,
    action,
    entity_type,
    instance,
    before=None,
    actor_user=None,
):
    after = None if action == AuditEvent.Action.DELETED else audit_snapshot(instance)
    if action == AuditEvent.Action.CREATED:
        changes = {"after": after}
    elif action == AuditEvent.Action.DELETED:
        changes = {"before": before or audit_snapshot(instance)}
    else:
        changes = {"before": before or {}, "after": after}

    actor_name = actor.full_name if actor else ""
    actor_email = ""
    if actor:
        actor_email = actor.email or (
            actor.user.email if actor.user_id else ""
        )
    elif actor_user:
        actor_name = actor_user.get_full_name() or actor_user.email
        actor_email = actor_user.email
    actor_name = actor_name or "Unknown member"
    description = str(instance)
    summary = f"{action.title()} {entity_type.replace('_', ' ')}: {description}"
    AuditEvent.objects.create(
        family=family,
        actor=actor,
        actor_name=actor_name,
        actor_email=actor_email,
        action=action,
        entity_type=entity_type,
        entity_id=str(instance.pk),
        summary=summary[:240],
        changes=changes,
    )

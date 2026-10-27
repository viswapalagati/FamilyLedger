from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def rupees(value):
    """Format a number as Indian rupees with lakh/crore-style grouping."""

    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return value

    negative = amount < 0
    amount = abs(amount).quantize(Decimal("0.01"))
    whole, _, frac = f"{amount:.2f}".partition(".")

    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups) + "," + tail

    return f"{'-' if negative else ''}₹{whole}.{frac}"


@register.filter
def pct(value, digits=1):
    try:
        return f"{float(value):.{int(digits)}f}%"
    except (TypeError, ValueError):
        return value


@register.filter
def signed_class(value):
    """CSS helper: 'amount-pos' / 'amount-neg' / 'amount-zero'."""

    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number > 0:
        return "amount-pos"
    if number < 0:
        return "amount-neg"
    return "amount-zero"


@register.simple_tag
def query_replace(request, **kwargs):
    """Return the current query string with ``kwargs`` replaced/added."""

    params = request.GET.copy()
    for key, value in kwargs.items():
        if value is None or value == "":
            params.pop(key, None)
        else:
            params[key] = value
    encoded = params.urlencode()
    return f"?{encoded}" if encoded else ""

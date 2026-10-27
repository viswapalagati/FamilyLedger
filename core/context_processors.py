"""Template context processor — SKELETON.

Implement per §14.1 (global shell) and §14.3.

``family_context`` must expose ``current_member``, ``current_family`` and
``is_family_admin`` to every template when the request user is an authenticated,
active family member. Until then it returns an empty dict, which makes
``base.html`` fall back to the logged-out (auth) layout.
"""


from urllib import request


def family_context(request):
    """Expose the current family member / family to every template."""

    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    member = user.family_member_or_none
    if member is None:
        return {}

    return {
        "current_member": member,
        "current_family": member.family,
        "is_family_admin": member.is_family_admin,
    }
    

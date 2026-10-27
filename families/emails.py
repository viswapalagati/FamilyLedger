"""families email helpers — SKELETON. Implement per §4.13 (FR-13.*) and §18-adjacent.

``send_account_created_email(member, added_by)``:
  * only when ``member.email`` is set
  * multipart: HTML body + plain-text alternative
  * templates: families/email/account_created.(html|txt)  (already provided)
  * MUST NOT contain the password (BR-17); include a login link built from
    ``settings.SITE_BASE_URL`` and optionally a password-reset link
  * a send failure must not raise to the caller (FR-13.4) -- caller handles it
"""

from django.conf import settings  # noqa: F401


def send_account_created_email(member, added_by):
    raise NotImplementedError("Implement per §4.13 (FR-13.*)")

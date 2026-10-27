"""Test factory helpers — SKELETON.

Build small helpers the test suite (§20) can reuse. Suggested signatures below;
implement them once the corresponding models exist.
"""


def make_family(name="Test Family", fy_start_month=4):
    raise NotImplementedError


def make_member(family, full_name="A Member", relationship="self", *,
                login=False, admin=False, email=None, password="Test@123",
                added_by=None):
    raise NotImplementedError


def make_head(family, name="Salary", kind="income", created_by=None):
    raise NotImplementedError


def make_txn(family, member, recorded_by, head, amount="1000", *,
             txn_type=None, when=None, merchant="Acme"):
    raise NotImplementedError

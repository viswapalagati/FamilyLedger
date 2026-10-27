"""families forms — SKELETON. Implement per §15 (rows AddMemberForm,
CreateLoginForm, MemberEditForm, ManageMemberForm, FamilySettingsForm) and
§4.2 (FR-2.*).
"""

from django import forms

from .models import Family, FamilyMember
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction


RELATIONSHIP_CHOICES = FamilyMember.Relationship.choices
User = get_user_model()

class _LoginFieldsMixin(forms.Form):
    email = forms.EmailField(required=False)
    password1 = forms.CharField(
        label="Password", widget=forms.PasswordInput, required=False,
        help_text="Only needed if this member should be able to log in.",
    )
    password2 = forms.CharField(
        label="Confirm password", widget=forms.PasswordInput, required=False
    )

    def _validate_login_block(self, cleaned, want_login):
        email = (cleaned.get("email") or "").lower()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if not want_login:
            return
        if not email:
            self.add_error("email", "An email is required to create a login.")
        elif User.objects.filter(email=email).exists():
            self.add_error("email", "An account with this email already exists.")
        if not p1:
            self.add_error("password1", "A password is required to create a login.")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "The two passwords do not match.")
        if p1:
            try:
                validate_password(p1)
            except forms.ValidationError as exc:
                self.add_error("password1", exc)

class AddMemberForm(forms.Form):
    """Add a person, optionally creating their login (FR-2.1-2.4).

    Fields: full_name, relationship, phone?, email?, date_of_birth?,
    need_account_creation (yes/no), password1?, password2?.
    ``__init__(self, *args, family=None, added_by=None, **kwargs)``.
    Yes  -> create User + FamilyMember(has_login=True); caller sends the email.
    No   -> create FamilyMember(user=None, has_login=False).
    """

    full_name = forms.CharField(max_length=120)
    relationship = forms.ChoiceField(choices=RELATIONSHIP_CHOICES)
    phone = forms.CharField(max_length=20, required=False)
    email = forms.EmailField(required=False)
    date_of_birth = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    need_account_creation = forms.TypedChoiceField(
        label="Create a login for this member?",
        choices=[("yes", "Yes — they can sign in"), ("no", "No — track only")],
        coerce=str,
        initial="no",
        widget=forms.Select(attrs={"data-need-account": "1"}),
    )
    password1 = forms.CharField(
        required=False, widget=forms.PasswordInput, label="Password"
    )
    password2 = forms.CharField(
        required=False, widget=forms.PasswordInput, label="Confirm password"
    )

    field_order = [
        "full_name", "relationship", "phone", "email", "date_of_birth",
        "need_account_creation", "password1", "password2",
    ]

    def __init__(self, *args, family=None, added_by=None, **kwargs):
        self.family = family
        self.added_by = added_by
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        want_login = cleaned.get("need_account_creation") == "yes"
        self._validate_login_block(cleaned, want_login)
        return cleaned

    def _validate_login_block(self, cleaned, want_login):
        if not want_login:
            return

        email = cleaned.get("email")
        if not email:
            self.add_error("email", "An email address is required to create a login.")
        elif User.objects.filter(email__iexact=email).exists():
            self.add_error("email", "An account with this email already exists.")

        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if not password1:
            self.add_error("password1", "A password is required to create a login.")
        else:
            try:
                validate_password(password1)
            except forms.ValidationError as error:
                self.add_error("password1", error)

        if not password2:
            self.add_error("password2", "Please confirm the password.")
        elif password1 and password1 != password2:
            self.add_error("password2", "The two passwords do not match.")

    @transaction.atomic
    def save(self):
        data = self.cleaned_data
        want_login = data["need_account_creation"] == "yes"
        user = None
        if want_login:
            first, _, last = data["full_name"].partition(" ")
            user = User.objects.create_user(
                email=data["email"].lower(),
                password=data["password1"],
                first_name=first,
                last_name=last,
                phone=data.get("phone", ""),
            )
        member = FamilyMember.objects.create(
            family=self.family,
            user=user,
            full_name=data["full_name"],
            email=(data.get("email") or "").lower(),
            phone=data.get("phone", ""),
            date_of_birth=data.get("date_of_birth"),
            relationship=data["relationship"],
            has_login=want_login,
            added_by=self.added_by,
            status=FamilyMember.Status.ACTIVE,
        )
        return member


class CreateLoginForm(_LoginFieldsMixin):
    """Give an existing login-less member a login (FR-2.8).

    ``__init__(self, *args, member=None, **kwargs)``; email + password required.
    """

    # TODO: fields, clean(), save() (create User, link, has_login=True)
    def __init__(self, *args, member=None, **kwargs):
        self.member = member 
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["password1"].required = True
        self.fields["password2"].required = True
        if member and member.email and not self.is_bound:
            self.fields["email"].initial = member.email

    def clean(self):
        cleaned =  super().clean()
        self._validate_login_block(cleaned, want_login=True)
        return cleaned

    @transaction.atomic
    def save(self):
        data = self.cleaned_data
        print("Data of email")
        first, _, last = self.member.full_name.partition(" ")
        user = User.objects.create_user(
            email=data["email"].lower(),
            password=data["password1"],
            first_name=first,
            last_name=last,
            phone=self.member.phone,
        )
        self.member.user = user
        self.member.email = data["email"].lower()
        self.member.has_login = True
        self.member.save(update_fields=["user", "email", "has_login", "updated_at"])
        return self.member



class MemberEditForm(forms.ModelForm):
    """Edit member details; sync the linked User (FR-2.7)."""

    class Meta:
        model = FamilyMember
        fields = ["full_name", "relationship", "phone", "email", "date_of_birth"]  
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"})}

        def save(self, commit=True):
            member = super().save(commit)
            if member.user_id:
                first, _,last = member.full_name.partition(" ")
                user = member.user
                user.first_name, user.last_name, user.phone = first, last, member.phone
                user.save(update_fields = ["first_name", "last_name", "phone"])
            return member



class ManageMemberForm(forms.ModelForm):
    """Admin-only: role + status (FR-2.9)."""

    class Meta:
        model = FamilyMember
        fields = ["is_family_admin", "status"]  # TODO: is_family_admin, status


class FamilySettingsForm(forms.ModelForm):
    """Family name + financial-year start month (FR-2.12)."""

    FY_MONTHS = [
        (1, "January"), (2, "February"), (3, "March"), (4, "April"),
        (5, "May"), (6, "June"), (7, "July"), (8, "August"),
        (9, "September"), (10, "October"), (11, "November"), (12, "December"),
    ]
    financial_year_start_month = forms.TypedChoiceField(choices=FY_MONTHS, coerce=int)

    class Meta:
        model = Family
        fields = ["name", "financial_year_start_month"]  # TODO §12.2: name, financial_year_start_month (month dropdown)

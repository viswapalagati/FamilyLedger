"""accounts forms — SKELETON. Implement per §15 (Forms Specification) rows
SignupForm / EmailAuthenticationForm / ProfileForm, and §4.1 / §4.3.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from families.models import Family, FamilyMember
from django.db import transaction


FY_MONTH_CHOICES = [
    (1, "January"), (2, "February"), (3, "March"), (4, "April"),
    (5, "May"), (6, "June"), (7, "July"), (8, "August"),
    (9, "September"), (10, "October"), (11, "November"), (12, "December"),
]



User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    """Same as Django's, just relabels the username field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email address"
        self.fields["username"].widget.attrs.update({"autofocus": True, "autocomplete": "email"})


class SignupForm(forms.Form):
    """Create the first user + their family + the founding member (FR-1.*, §15).

    Fields: first_name, last_name?, email, phone?, password1, password2,
    family_name, financial_year_start_month (1-12, default 4).
    ``save()`` must be atomic and create User -> Family -> FamilyMember(self,
    admin, has_login) -> set added_by=self and Family.created_by.
    """

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    first_name = forms.CharField(max_length=60)
    last_name = forms.CharField(max_length=50, required=False)
    email = forms.EmailField()
    phone = forms.CharField(max_length=30, required=False)
    password1 = forms.CharField(widget=forms.PasswordInput, min_length=8, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, min_length=8, label="Confirm password")
    family_name = forms.CharField(max_length=100, label="Family name")
    financial_year_start_month = forms.TypedChoiceField(
            choices=FY_MONTH_CHOICES, coerce=int, initial=4, label="Financial year starts in"
        )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "The two passwords do not match.")
        if p1:
            validate_password(p1)
        return cleaned

    
    @transaction.atomic 
    def save(self):
        """Create User, Family, and FamilyMember atomically."""
        data = self.cleaned_data
        user = User.objects.create_user(
            email=data["email"],
            password=data["password1"],
            first_name=data["first_name"],
            last_name=data.get("last_name", ""),
            phone=data.get("phone", ""),
        )
        family = Family.objects.create(
            name=data["family_name"],
            financial_year_start_month=data["financial_year_start_month"],
        )
        member = FamilyMember.objects.create(
            family=family,
            user=user,
            full_name=user.get_full_name(),
            email=user.email,
            phone=user.phone,
            relationship=FamilyMember.Relationship.SELF,
            has_login=True,
            is_family_admin=True,
            status=FamilyMember.Status.ACTIVE,
        )
        member.added_by = member
        member.save(update_fields=["added_by"])
        family.created_by = member
        family.save(update_fields=["created_by"])
        return user 

    # TODO: declare fields, clean_email(), clean(), save()


class ProfileForm(forms.ModelForm):
    """Edit first_name / last_name / phone; keep the FamilyMember in sync (§4.3)."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone"]  # TODO §12.1: ["first_name", "last_name", "phone"]

        def save(self, commit=True):
            user = super().save(commit)
            member = user.family_member_or_none
            if member:
                member.full_name = user.get_full_name()
                member.phone = user.phone
                member.save(update_fields=["full_name", "phone", "updated_at"])
            return user

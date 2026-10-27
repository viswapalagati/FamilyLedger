from django import forms


class FamilyModelForm(forms.ModelForm):
    """Base ModelForm that is family-aware.

    Subclasses receive ``self.family`` and ``self.acting_member`` and are
    expected to narrow any ``ModelChoiceField`` querysets to ``self.family`` in
    their own ``__init__`` (call ``super().__init__`` first).
    """

    def __init__(self, *args, family=None, acting_member=None, **kwargs):
        self.family = family
        self.acting_member = acting_member
        super().__init__(*args, **kwargs)

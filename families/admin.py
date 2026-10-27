"""families admin — SKELETON (FR-14.1).

Register Family and FamilyMember with useful list_display / list_filter /
search_fields / autocomplete_fields. See §14.
"""

from django.contrib import admin

from .models import Family, FamilyMember


class FamilyMemberInline(admin.TabularInline):
    model = FamilyMember
    fk_name = "family"
    extra = 0
    fields = ["full_name", "relationship", "email", "has_login", "is_family_admin", "status"]
    show_change_link = True


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ["name", "financial_year_start_month", "created_at"]
    search_fields = ["name"]
    inlines = [FamilyMemberInline]


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ["full_name", "family", "relationship", "has_login", "is_family_admin", "status"]
    list_filter = ["family", "relationship", "has_login", "is_family_admin", "status"]
    search_fields = ["full_name", "email"]
    autocomplete_fields = ["user", "added_by"]
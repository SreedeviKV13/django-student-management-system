from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "roll_number",
        "full_name",
        "email",
        "department",
        "course",
        "academic_year",
        "admission_date",
    )
    list_filter = ("department", "course", "academic_year", "gender", "admission_date")
    search_fields = ("roll_number", "full_name", "email", "phone_number")
    ordering = ("roll_number",)
    date_hierarchy = "admission_date"
    list_per_page = 25
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Personal information", {"fields": ("roll_number", "full_name", "gender", "date_of_birth")}),
        ("Contact", {"fields": ("email", "phone_number", "address")}),
        ("Academic information", {"fields": ("department", "course", "academic_year", "admission_date")}),
        ("Record details", {"fields": ("created_at", "updated_at")}),
    )

from django import forms

from .models import Student


class StudentForm(forms.ModelForm):
    """Add / edit form for a student, styled with Bootstrap 5."""

    class Meta:
        model = Student
        fields = [
            "roll_number",
            "full_name",
            "email",
            "phone_number",
            "gender",
            "date_of_birth",
            "department",
            "course",
            "academic_year",
            "admission_date",
            "address",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "admission_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "address": forms.Textarea(attrs={"rows": 3}),
            "phone_number": forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "full_name": forms.TextInput(attrs={"autocomplete": "name"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css_class
        self.fields["roll_number"].widget.attrs["placeholder"] = "CS2024001"
        self.fields["full_name"].widget.attrs["placeholder"] = "e.g. Anjali Menon"
        self.fields["email"].widget.attrs["placeholder"] = "name@example.com"

    def clean_roll_number(self):
        return self.cleaned_data["roll_number"].strip().upper()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def full_clean(self):
        """Mark fields that have errors so Bootstrap and screen readers show them."""
        super().full_clean()
        for name in self.errors:
            if name in self.fields:
                attrs = self.fields[name].widget.attrs
                attrs["class"] = f"{attrs.get('class', '')} is-invalid".strip()
                attrs["aria-invalid"] = "true"
                attrs["aria-describedby"] = f"id_{name}-error"


class StudentFilterForm(forms.Form):
    """GET form used on the student list page for searching and filtering."""

    q = forms.CharField(
        required=False,
        max_length=100,
        label="Search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Name, roll number or email",
                "type": "search",
            }
        ),
    )
    department = forms.ChoiceField(
        required=False,
        label="Department",
        choices=[("", "All departments")] + Student.Department.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    course = forms.ChoiceField(
        required=False,
        label="Course",
        choices=[("", "All courses")] + Student.Course.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    academic_year = forms.ChoiceField(
        required=False,
        label="Academic year",
        choices=[("", "All years")] + Student.AcademicYear.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

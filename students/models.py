from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Q
from django.urls import reverse
from django.utils import timezone


def validate_not_in_future(value):
    """Dates such as date of birth or admission cannot be in the future."""
    if value > timezone.localdate():
        raise ValidationError("This date cannot be in the future.")


roll_number_validator = RegexValidator(
    regex=r"^[A-Za-z0-9][A-Za-z0-9/\-]*$",
    message="Use only letters, numbers, hyphens or slashes (for example CS2024001).",
)

# Rejects digits and common symbols but still allows names in any language.
full_name_validator = RegexValidator(
    regex=r"^[^0-9@#$%^&*()_+=\[\]{};:\"\\|<>/?~`!]+$",
    message="Name can contain letters, spaces, dots, apostrophes and hyphens only.",
)

phone_validator = RegexValidator(
    regex=r"^\+?[0-9]{10,15}$",
    message="Enter 10 to 15 digits, with an optional leading + (no spaces or dashes).",
)


class Student(models.Model):
    """A single student record."""

    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"

    class Department(models.TextChoices):
        CSE = "CSE", "Computer Science & Engineering"
        IT = "IT", "Information Technology"
        ECE = "ECE", "Electronics & Communication"
        EEE = "EEE", "Electrical & Electronics"
        ME = "ME", "Mechanical Engineering"
        CE = "CE", "Civil Engineering"
        BUS = "BUS", "Business Administration"
        SCI = "SCI", "Applied Sciences"

    class Course(models.TextChoices):
        BTECH = "BTECH", "B.Tech"
        MTECH = "MTECH", "M.Tech"
        BCA = "BCA", "BCA"
        MCA = "MCA", "MCA"
        BSC = "BSC", "B.Sc"
        MSC = "MSC", "M.Sc"
        BBA = "BBA", "BBA"
        MBA = "MBA", "MBA"
        DIPLOMA = "DIPLOMA", "Diploma"

    class AcademicYear(models.IntegerChoices):
        FIRST = 1, "First Year"
        SECOND = 2, "Second Year"
        THIRD = 3, "Third Year"
        FOURTH = 4, "Fourth Year"

    roll_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[roll_number_validator],
        help_text="Unique ID, e.g. CS2024001. Saved in capital letters.",
        error_messages={"unique": "A student with this roll number already exists."},
    )
    full_name = models.CharField(max_length=100, validators=[full_name_validator])
    email = models.EmailField(
        unique=True,
        error_messages={"unique": "A student with this email address already exists."},
    )
    phone_number = models.CharField(
        max_length=16,
        validators=[phone_validator],
        help_text="Digits only, with an optional leading +. Example: +919876543210",
    )
    gender = models.CharField(max_length=1, choices=Gender.choices)
    date_of_birth = models.DateField(validators=[validate_not_in_future])
    department = models.CharField(max_length=10, choices=Department.choices)
    course = models.CharField(max_length=10, choices=Course.choices)
    academic_year = models.PositiveSmallIntegerField(choices=AcademicYear.choices)
    admission_date = models.DateField(validators=[validate_not_in_future])
    address = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["roll_number"]
        indexes = [
            models.Index(fields=["department"]),
            models.Index(fields=["course"]),
            models.Index(fields=["academic_year"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(admission_date__gt=F("date_of_birth")),
                name="student_admission_after_birth",
                violation_error_message="Admission date must be after the date of birth.",
            ),
        ]

    def __str__(self):
        return f"{self.roll_number} - {self.full_name}"

    def get_absolute_url(self):
        return reverse("students:detail", kwargs={"pk": self.pk})

    def _normalize(self):
        """Keep stored values consistent so uniqueness checks are reliable."""
        self.roll_number = (self.roll_number or "").strip().upper()
        self.email = (self.email or "").strip().lower()
        self.full_name = " ".join((self.full_name or "").split())

    def clean(self):
        super().clean()
        self._normalize()
        if self.date_of_birth and self.admission_date and self.admission_date <= self.date_of_birth:
            raise ValidationError(
                {"admission_date": "Admission date must be after the date of birth."}
            )

    def save(self, *args, **kwargs):
        self._normalize()
        super().save(*args, **kwargs)

    @property
    def age(self):
        today = timezone.localdate()
        born = self.date_of_birth
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    @property
    def initials(self):
        parts = self.full_name.split()
        return "".join(part[0] for part in parts[:2]).upper() or "?"

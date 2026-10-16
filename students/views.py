from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.views.decorators.http import require_http_methods

from .forms import StudentFilterForm, StudentForm
from .models import Student

STUDENTS_PER_PAGE = 10


def _distribution(field_name, choices, total):
    """Count students per value of ``field_name`` for the dashboard."""
    labels = dict(choices)
    rows = (
        Student.objects.order_by()
        .values(field_name)
        .annotate(total=Count("id"))
        .order_by("-total", field_name)
    )
    return [
        {
            "label": labels.get(row[field_name], row[field_name]),
            "count": row["total"],
            "percent": round(row["total"] * 100 / total) if total else 0,
        }
        for row in rows
    ]


def dashboard(request):
    """Statistics and recent activity, all calculated from the database."""
    students = Student.objects.all()
    total = students.count()
    current_year = timezone.localdate().year

    department_stats = _distribution("department", Student.Department.choices, total)
    year_stats = _distribution("academic_year", Student.AcademicYear.choices, total)

    context = {
        "total_students": total,
        "total_departments": students.order_by().values("department").distinct().count(),
        "total_courses": students.order_by().values("course").distinct().count(),
        "current_year": current_year,
        "current_year_admissions": students.filter(admission_date__year=current_year).count(),
        "recent_students": students.order_by("-created_at", "-id")[:5],
        "department_stats": department_stats,
        "year_stats": year_stats,
        # Passed to Chart.js with json_script (the page still works without it).
        "chart_data": {
            "departments": {
                "labels": [item["label"] for item in department_stats],
                "values": [item["count"] for item in department_stats],
            },
            "years": {
                "labels": [item["label"] for item in year_stats],
                "values": [item["count"] for item in year_stats],
            },
        },
    }
    return render(request, "students/dashboard.html", context)


def student_list(request):
    """Searchable, filterable and paginated list of students."""
    filter_form = StudentFilterForm(request.GET)
    filter_form.is_valid()  # invalid fields are simply left out of cleaned_data
    data = filter_form.cleaned_data

    students = Student.objects.all()

    search = (data.get("q") or "").strip()
    if search:
        students = students.filter(
            Q(full_name__icontains=search)
            | Q(roll_number__icontains=search)
            | Q(email__icontains=search)
        )
    if data.get("department"):
        students = students.filter(department=data["department"])
    if data.get("course"):
        students = students.filter(course=data["course"])
    if data.get("academic_year"):
        students = students.filter(academic_year=data["academic_year"])

    filters_active = any(
        [search, data.get("department"), data.get("course"), data.get("academic_year")]
    )

    paginator = Paginator(students, STUDENTS_PER_PAGE)
    # get_page() copes with missing, non-numeric or out-of-range page numbers.
    page_obj = paginator.get_page(request.GET.get("page"))
    page_range = list(
        paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)
    )

    # Search/filter parameters (without "page") so pagination links keep them.
    kept_params = {key: value for key, value in request.GET.items() if value and key != "page"}

    context = {
        "filter_form": filter_form,
        "page_obj": page_obj,
        "page_range": page_range,
        "ellipsis": paginator.ELLIPSIS,
        "total_results": paginator.count,
        "filters_active": filters_active,
        "query_string": urlencode(kept_params),
    }
    return render(request, "students/student_list.html", context)


def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return render(request, "students/student_detail.html", {"student": student})


def student_create(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            messages.success(request, f"{student.full_name} was added successfully.")
            return redirect("students:detail", pk=student.pk)
        messages.error(request, "The student could not be saved. Please fix the errors below.")
    else:
        form = StudentForm()
    context = {
        "form": form,
        "page_title": "Add Student",
        "submit_label": "Save Student",
        "cancel_url": reverse("students:list"),
    }
    return render(request, "students/student_form.html", context)


def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            student = form.save()
            messages.success(request, f"{student.full_name} was updated successfully.")
            return redirect("students:detail", pk=student.pk)
        messages.error(request, "The changes could not be saved. Please fix the errors below.")
    else:
        form = StudentForm(instance=student)
    context = {
        "form": form,
        "student": student,
        "page_title": "Edit Student",
        "submit_label": "Save Changes",
        "cancel_url": student.get_absolute_url(),
    }
    return render(request, "students/student_form.html", context)


@require_http_methods(["GET", "POST"])
def student_delete(request, pk):
    """GET shows a confirmation page; only a POST (with CSRF token) deletes."""
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        name = student.full_name
        student.delete()
        messages.success(request, f"{name} was deleted.")
        return redirect("students:list")
    return render(request, "students/student_confirm_delete.html", {"student": student})

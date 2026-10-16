from datetime import date, timedelta
from itertools import count

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import resolve, reverse
from django.utils import timezone

from .forms import StudentFilterForm, StudentForm
from .models import Student

_counter = count(1)


def _letters(n):
    """1 -> 'A', 2 -> 'B', 27 -> 'AA' (names may not contain digits)."""
    result = ""
    while n:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result


def student_data(**overrides):
    """Valid form/model data for one student; each call gets a unique roll no. and email."""
    n = next(_counter)
    data = {
        "roll_number": f"CS2024{n:03d}",
        "full_name": f"Test Student {_letters(n)}",
        "email": f"student{n}@example.com",
        "phone_number": "9876543210",
        "gender": Student.Gender.FEMALE,
        "date_of_birth": date(2004, 5, 10),
        "department": Student.Department.CSE,
        "course": Student.Course.BTECH,
        "academic_year": Student.AcademicYear.FIRST,
        "admission_date": date(2023, 8, 1),
        "address": "12 Main Street, Kannur, Kerala",
    }
    data.update(overrides)
    return data


def make_student(**overrides):
    return Student.objects.create(**student_data(**overrides))


class StudentModelTests(TestCase):
    def test_create_student_and_str(self):
        student = make_student(roll_number="CS001", full_name="Anjali Menon")
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(str(student), "CS001 - Anjali Menon")
        self.assertIsNotNone(student.created_at)
        self.assertIsNotNone(student.updated_at)

    def test_roll_number_must_be_unique(self):
        make_student(roll_number="CS001")
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_student(roll_number="CS001")

    def test_roll_number_uniqueness_ignores_case(self):
        make_student(roll_number="cs001")
        self.assertEqual(Student.objects.get().roll_number, "CS001")
        duplicate = Student(**student_data(roll_number="Cs001"))
        with self.assertRaises(ValidationError) as ctx:
            duplicate.full_clean()
        self.assertIn("roll_number", ctx.exception.message_dict)

    def test_email_must_be_unique(self):
        make_student(email="same@example.com")
        duplicate = Student(**student_data(email="SAME@example.com"))
        with self.assertRaises(ValidationError) as ctx:
            duplicate.full_clean()
        self.assertIn("email", ctx.exception.message_dict)

    def test_invalid_phone_rejected(self):
        student = Student(**student_data(phone_number="12345"))
        with self.assertRaises(ValidationError) as ctx:
            student.full_clean()
        self.assertIn("phone_number", ctx.exception.message_dict)

    def test_future_dates_rejected(self):
        tomorrow = timezone.localdate() + timedelta(days=1)
        student = Student(**student_data(date_of_birth=tomorrow, admission_date=tomorrow))
        with self.assertRaises(ValidationError) as ctx:
            student.full_clean()
        self.assertIn("date_of_birth", ctx.exception.message_dict)
        self.assertIn("admission_date", ctx.exception.message_dict)

    def test_admission_must_be_after_birth(self):
        student = Student(
            **student_data(date_of_birth=date(2005, 1, 1), admission_date=date(2004, 1, 1))
        )
        with self.assertRaises(ValidationError) as ctx:
            student.full_clean()
        self.assertIn("admission_date", ctx.exception.message_dict)

    def test_database_constraint_blocks_bad_dates(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_student(date_of_birth=date(2005, 1, 1), admission_date=date(2004, 1, 1))

    def test_age_and_initials(self):
        today = timezone.localdate()
        born = date(today.year - 20, today.month, 1)
        student = make_student(full_name="Anjali Menon", date_of_birth=born)
        self.assertEqual(student.age, 20)
        self.assertEqual(student.initials, "AM")

    def test_absolute_url(self):
        student = make_student()
        self.assertEqual(student.get_absolute_url(), reverse("students:detail", args=[student.pk]))


class StudentFormTests(TestCase):
    def test_valid_form(self):
        form = StudentForm(data=student_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_required_fields(self):
        form = StudentForm(data={})
        self.assertFalse(form.is_valid())
        for field in StudentForm.Meta.fields:
            self.assertIn(field, form.errors)

    def test_duplicate_roll_number_shows_error(self):
        make_student(roll_number="CS001")
        form = StudentForm(data=student_data(roll_number="cs001"))
        self.assertFalse(form.is_valid())
        self.assertIn("roll_number", form.errors)
        self.assertIn("already exists", form.errors["roll_number"][0])

    def test_duplicate_email_shows_error(self):
        make_student(email="taken@example.com")
        form = StudentForm(data=student_data(email="taken@example.com"))
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_invalid_email_and_phone(self):
        form = StudentForm(data=student_data(email="not-an-email", phone_number="abc"))
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertIn("phone_number", form.errors)

    def test_invalid_choices(self):
        form = StudentForm(data=student_data(department="XYZ", academic_year=9, gender="Q"))
        self.assertFalse(form.is_valid())
        self.assertIn("department", form.errors)
        self.assertIn("academic_year", form.errors)
        self.assertIn("gender", form.errors)

    def test_future_birth_date_rejected(self):
        future = timezone.localdate() + timedelta(days=5)
        form = StudentForm(data=student_data(date_of_birth=future))
        self.assertFalse(form.is_valid())
        self.assertIn("date_of_birth", form.errors)

    def test_admission_before_birth_rejected(self):
        form = StudentForm(
            data=student_data(date_of_birth=date(2005, 1, 1), admission_date=date(2004, 1, 1))
        )
        self.assertFalse(form.is_valid())
        self.assertIn("admission_date", form.errors)

    def test_editing_keeps_own_roll_number(self):
        student = make_student(roll_number="CS001")
        data = student_data(roll_number="CS001", email=student.email, full_name="New Name")
        form = StudentForm(data=data, instance=student)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_fields_are_marked_for_accessibility(self):
        form = StudentForm(data=student_data(email="bad"))
        form.is_valid()
        attrs = form.fields["email"].widget.attrs
        self.assertIn("is-invalid", attrs["class"])
        self.assertEqual(attrs["aria-invalid"], "true")

    def test_filter_form_ignores_invalid_values(self):
        form = StudentFilterForm({"department": "NOPE", "q": "abc"})
        form.is_valid()
        self.assertNotIn("department", form.cleaned_data)
        self.assertEqual(form.cleaned_data["q"], "abc")


class UrlTests(TestCase):
    def test_named_urls_resolve(self):
        expectations = {
            reverse("students:dashboard"): "dashboard",
            reverse("students:list"): "student_list",
            reverse("students:create"): "student_create",
            reverse("students:detail", args=[1]): "student_detail",
            reverse("students:update", args=[1]): "student_update",
            reverse("students:delete", args=[1]): "student_delete",
        }
        for url, view_name in expectations.items():
            self.assertEqual(resolve(url).func.__name__, view_name)

    def test_url_paths(self):
        self.assertEqual(reverse("students:dashboard"), "/")
        self.assertEqual(reverse("students:list"), "/students/")
        self.assertEqual(reverse("students:create"), "/students/add/")


class DashboardTests(TestCase):
    def test_empty_state(self):
        response = self.client.get(reverse("students:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "students/dashboard.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertEqual(response.context["total_students"], 0)
        self.assertContains(response, "No students yet")
        self.assertContains(response, "No data to show yet")

    def test_statistics_come_from_database(self):
        this_year = timezone.localdate().year
        make_student(department="CSE", course="BTECH", academic_year=1,
                     admission_date=date(this_year, 1, 1))
        make_student(department="CSE", course="MTECH", academic_year=2,
                     admission_date=date(2020, 8, 1))
        make_student(department="ECE", course="BTECH", academic_year=2,
                     admission_date=date(2020, 8, 1))

        response = self.client.get(reverse("students:dashboard"))
        context = response.context
        self.assertEqual(context["total_students"], 3)
        self.assertEqual(context["total_departments"], 2)
        self.assertEqual(context["total_courses"], 2)
        self.assertEqual(context["current_year_admissions"], 1)

        by_department = {item["label"]: item["count"] for item in context["department_stats"]}
        self.assertEqual(by_department["Computer Science & Engineering"], 2)
        self.assertEqual(by_department["Electronics & Communication"], 1)

        by_year = {item["label"]: item["count"] for item in context["year_stats"]}
        self.assertEqual(by_year, {"First Year": 1, "Second Year": 2})

        chart = context["chart_data"]["departments"]
        self.assertEqual(sum(chart["values"]), 3)
        self.assertContains(response, 'id="chart-data"')

    def test_recent_students_limited_to_five_newest_first(self):
        students = [make_student() for _ in range(7)]
        response = self.client.get(reverse("students:dashboard"))
        recent = list(response.context["recent_students"])
        self.assertEqual(len(recent), 5)
        self.assertEqual(recent[0], students[-1])


class StudentCrudTests(TestCase):
    def test_create_page_loads(self):
        response = self.client.get(reverse("students:create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "students/student_form.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_create_student_success(self):
        data = student_data(roll_number="new001", full_name="Ravi Kumar")
        response = self.client.post(reverse("students:create"), data, follow=True)
        student = Student.objects.get(roll_number="NEW001")
        self.assertRedirects(response, reverse("students:detail", args=[student.pk]))
        self.assertContains(response, "Ravi Kumar was added successfully.")

    def test_create_student_invalid_shows_errors(self):
        data = student_data(email="bad-email")
        response = self.client.post(reverse("students:create"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Student.objects.count(), 0)
        self.assertContains(response, "Enter a valid email address.")
        self.assertContains(response, "Please fix the errors below")

    def test_create_duplicate_roll_number_rejected(self):
        make_student(roll_number="CS001")
        response = self.client.post(reverse("students:create"), student_data(roll_number="CS001"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Student.objects.count(), 1)
        self.assertContains(response, "A student with this roll number already exists.")

    def test_detail_page(self):
        student = make_student(full_name="Anjali Menon")
        response = self.client.get(reverse("students:detail", args=[student.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "students/student_detail.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertContains(response, "Anjali Menon")
        self.assertContains(response, student.email)

    def test_detail_missing_student_returns_404(self):
        response = self.client.get(reverse("students:detail", args=[9999]))
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")

    def test_update_page_prefills_form(self):
        student = make_student(full_name="Anjali Menon", date_of_birth=date(2004, 5, 10))
        response = self.client.get(reverse("students:update", args=[student.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Anjali Menon"')
        self.assertContains(response, 'value="2004-05-10"')

    def test_update_student_success(self):
        student = make_student(full_name="Old Name")
        data = student_data(roll_number=student.roll_number, email=student.email, full_name="New Name")
        response = self.client.post(reverse("students:update", args=[student.pk]), data, follow=True)
        student.refresh_from_db()
        self.assertEqual(student.full_name, "New Name")
        self.assertContains(response, "New Name was updated successfully.")

    def test_update_invalid_does_not_change_student(self):
        student = make_student(full_name="Old Name")
        data = student_data(roll_number=student.roll_number, email="bad", full_name="New Name")
        response = self.client.post(reverse("students:update", args=[student.pk]), data)
        self.assertEqual(response.status_code, 200)
        student.refresh_from_db()
        self.assertEqual(student.full_name, "Old Name")

    def test_update_missing_student_returns_404(self):
        self.assertEqual(self.client.get(reverse("students:update", args=[9999])).status_code, 404)

    def test_delete_confirmation_page_does_not_delete(self):
        student = make_student()
        response = self.client.get(reverse("students:delete", args=[student.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "students/student_confirm_delete.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertTrue(Student.objects.filter(pk=student.pk).exists())

    def test_delete_with_post(self):
        student = make_student(full_name="Delete Me")
        response = self.client.post(reverse("students:delete", args=[student.pk]), follow=True)
        self.assertRedirects(response, reverse("students:list"))
        self.assertFalse(Student.objects.filter(pk=student.pk).exists())
        self.assertContains(response, "Delete Me was deleted.")

    def test_delete_requires_csrf_token(self):
        from django.test import Client

        student = make_student()
        strict_client = Client(enforce_csrf_checks=True)
        response = strict_client.post(reverse("students:delete", args=[student.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Student.objects.filter(pk=student.pk).exists())

    def test_delete_rejects_other_methods(self):
        student = make_student()
        response = self.client.put(reverse("students:delete", args=[student.pk]))
        self.assertEqual(response.status_code, 405)

    def test_delete_missing_student_returns_404(self):
        response = self.client.post(reverse("students:delete", args=[9999]))
        self.assertEqual(response.status_code, 404)


class StudentListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.anjali = make_student(
            roll_number="CS001", full_name="Anjali Menon", email="anjali@example.com",
            department="CSE", course="BTECH", academic_year=1,
        )
        cls.ravi = make_student(
            roll_number="EC002", full_name="Ravi Kumar", email="ravi@college.edu",
            department="ECE", course="BTECH", academic_year=2,
        )
        cls.meera = make_student(
            roll_number="CS003", full_name="Meera Nair", email="meera@example.com",
            department="CSE", course="MTECH", academic_year=2,
        )

    def get_students(self, **params):
        response = self.client.get(reverse("students:list"), params)
        self.assertEqual(response.status_code, 200)
        return response, list(response.context["page_obj"].object_list)

    def test_list_page_uses_templates(self):
        response, students = self.get_students()
        self.assertTemplateUsed(response, "students/student_list.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertEqual(len(students), 3)

    def test_search_by_name(self):
        _, students = self.get_students(q="anjali")
        self.assertEqual(students, [self.anjali])

    def test_search_by_roll_number(self):
        _, students = self.get_students(q="ec002")
        self.assertEqual(students, [self.ravi])

    def test_search_by_email(self):
        _, students = self.get_students(q="college.edu")
        self.assertEqual(students, [self.ravi])

    def test_filter_by_department(self):
        _, students = self.get_students(department="CSE")
        self.assertEqual(set(students), {self.anjali, self.meera})

    def test_filter_by_course(self):
        _, students = self.get_students(course="MTECH")
        self.assertEqual(students, [self.meera])

    def test_filter_by_academic_year(self):
        _, students = self.get_students(academic_year="2")
        self.assertEqual(set(students), {self.ravi, self.meera})

    def test_combined_search_and_filters(self):
        _, students = self.get_students(q="example.com", department="CSE", academic_year="2")
        self.assertEqual(students, [self.meera])

    def test_no_results_shows_empty_state(self):
        response, students = self.get_students(q="nobody-has-this-name")
        self.assertEqual(students, [])
        self.assertContains(response, "No students match your search.")
        self.assertContains(response, "Clear filters")

    def test_invalid_filter_value_is_ignored(self):
        _, students = self.get_students(department="NOT-A-DEPARTMENT")
        self.assertEqual(len(students), 3)

    def test_clear_button_links_to_unfiltered_list(self):
        response, _ = self.get_students(q="anjali")
        self.assertContains(response, f'href="{reverse("students:list")}"')
        self.assertTrue(response.context["filters_active"])

    def test_filter_choices_selected_in_form(self):
        response, _ = self.get_students(department="CSE")
        self.assertContains(response, '<option value="CSE" selected>')

    def test_empty_database_shows_add_prompt(self):
        Student.objects.all().delete()
        response = self.client.get(reverse("students:list"))
        self.assertContains(response, "There are no students yet.")
        self.assertFalse(response.context["filters_active"])


class PaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for i in range(1, 26):  # 25 students -> 3 pages of 10
            make_student(
                roll_number=f"PG{i:03d}",
                full_name=f"Paged Student {i:02d}",
                department="CSE" if i % 2 else "ECE",
            )

    def test_first_page_has_ten_students(self):
        response = self.client.get(reverse("students:list"))
        page = response.context["page_obj"]
        self.assertEqual(len(page.object_list), 10)
        self.assertEqual(page.paginator.num_pages, 3)
        self.assertContains(response, "Showing 1&ndash;10 of 25")

    def test_second_and_last_page(self):
        page2 = self.client.get(reverse("students:list"), {"page": 2}).context["page_obj"]
        self.assertEqual(page2.number, 2)
        page3 = self.client.get(reverse("students:list"), {"page": 3}).context["page_obj"]
        self.assertEqual(len(page3.object_list), 5)

    def test_invalid_page_numbers_do_not_crash(self):
        url = reverse("students:list")
        self.assertEqual(self.client.get(url, {"page": "abc"}).context["page_obj"].number, 1)
        self.assertEqual(self.client.get(url, {"page": "0"}).context["page_obj"].number, 3)
        self.assertEqual(self.client.get(url, {"page": "999"}).context["page_obj"].number, 3)
        self.assertEqual(self.client.get(url, {"page": ""}).context["page_obj"].number, 1)

    def test_pagination_links_keep_search_and_filters(self):
        response = self.client.get(reverse("students:list"), {"department": "CSE", "q": "Paged"})
        self.assertEqual(response.context["total_results"], 13)  # odd numbers 1..25
        self.assertEqual(response.context["page_obj"].paginator.num_pages, 2)
        self.assertContains(response, "department=CSE")
        self.assertContains(response, "q=Paged")
        self.assertContains(response, "&amp;page=2")

    def test_no_pagination_for_single_page(self):
        response = self.client.get(reverse("students:list"), {"q": "Student 07"})
        self.assertEqual(response.context["total_results"], 1)
        self.assertNotContains(response, "Student list pages")

    def test_empty_results_with_page_param(self):
        response = self.client.get(reverse("students:list"), {"q": "zzz", "page": 4})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_results"], 0)


class AdminTests(TestCase):
    def test_admin_pages_load(self):
        user = get_user_model().objects.create_superuser("admin", "admin@example.com", "pass12345")
        self.client.force_login(user)
        student = make_student()
        self.assertEqual(self.client.get(reverse("admin:students_student_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:students_student_add")).status_code, 200)
        change_url = reverse("admin:students_student_change", args=[student.pk])
        self.assertEqual(self.client.get(change_url).status_code, 200)

    def test_admin_search(self):
        user = get_user_model().objects.create_superuser("admin", "admin@example.com", "pass12345")
        self.client.force_login(user)
        make_student(full_name="Findable Person")
        response = self.client.get(reverse("admin:students_student_changelist"), {"q": "Findable"})
        self.assertContains(response, "Findable Person")


class SharedTemplateTests(TestCase):
    def test_every_page_extends_base_and_has_navigation(self):
        student = make_student()
        urls = [
            reverse("students:dashboard"),
            reverse("students:list"),
            reverse("students:create"),
            reverse("students:detail", args=[student.pk]),
            reverse("students:update", args=[student.pk]),
            reverse("students:delete", args=[student.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "base.html")
                self.assertContains(response, 'aria-label="Main navigation"')
                self.assertContains(response, "students/css/style.css")

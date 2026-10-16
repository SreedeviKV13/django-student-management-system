"""Adds 15 sample students. Safe to run more than once (it updates by roll number).

Run from the project folder (where manage.py is):
    python manage.py shell -c "exec(open('seed_students.py', encoding='utf-8').read())"
"""
from datetime import date

from students.models import Student

SAMPLE_STUDENTS = [
    # roll_number, full_name, gender, date_of_birth, department, course, year, admission_date
    ("CS2026001", "Anjali Menon", "F", date(2008, 3, 14), "CSE", "BTECH", 1, date(2026, 8, 1)),
    ("CS2026002", "Arjun Nair", "M", date(2008, 7, 22), "CSE", "BTECH", 1, date(2026, 8, 1)),
    ("EC2026001", "Fathima Rahman", "F", date(2008, 1, 9), "ECE", "BTECH", 1, date(2026, 8, 2)),
    ("CS2025001", "Rahul Krishnan", "M", date(2007, 11, 5), "CSE", "BTECH", 2, date(2025, 8, 4)),
    ("IT2025001", "Sneha Varghese", "F", date(2007, 5, 30), "IT", "BTECH", 2, date(2025, 8, 4)),
    ("ME2025001", "Vishnu Prasad", "M", date(2007, 9, 18), "ME", "BTECH", 2, date(2025, 8, 5)),
    ("CA2025001", "Devika Suresh", "F", date(2006, 12, 2), "CSE", "BCA", 2, date(2025, 7, 28)),
    ("CS2024001", "Mohammed Ashraf", "M", date(2006, 4, 25), "CSE", "BTECH", 3, date(2024, 8, 5)),
    ("EE2024001", "Lakshmi Pillai", "F", date(2006, 8, 11), "EEE", "BTECH", 3, date(2024, 8, 5)),
    ("CE2024001", "Nithin George", "M", date(2006, 2, 19), "CE", "BTECH", 3, date(2024, 8, 6)),
    ("MC2024001", "Gayathri Mohan", "F", date(2002, 6, 7), "CSE", "MCA", 2, date(2024, 8, 12)),
    ("CS2023001", "Aswin Kumar", "M", date(2005, 10, 3), "CSE", "BTECH", 4, date(2023, 8, 7)),
    ("EC2023001", "Hana Basheer", "F", date(2005, 3, 21), "ECE", "BTECH", 4, date(2023, 8, 7)),
    ("BU2024001", "Joseph Thomas", "M", date(2005, 7, 15), "BUS", "BBA", 3, date(2024, 7, 29)),
    ("SC2025001", "Amrita Dev", "F", date(2007, 1, 28), "SCI", "BSC", 2, date(2025, 7, 30)),
]

created = updated = 0
for index, (roll, name, gender, dob, dept, course, year, admitted) in enumerate(SAMPLE_STUDENTS, start=1):
    first = name.split()[0].lower()
    student = Student.objects.filter(roll_number=roll).first() or Student(roll_number=roll)
    was_new = student.pk is None
    student.full_name = name
    student.email = f"{first}.{roll.lower()}@example.com"
    student.phone_number = f"98470{10000 + index * 137:05d}"
    student.gender = gender
    student.date_of_birth = dob
    student.department = dept
    student.course = course
    student.academic_year = year
    student.admission_date = admitted
    student.address = f"{index + 10}, Lake View Road, Taliparamba, Kannur, Kerala"
    student.full_clean()  # same validation as the web form
    student.save()
    created += was_new
    updated += not was_new

print(f"Done: {created} created, {updated} updated. Total students: {Student.objects.count()}")
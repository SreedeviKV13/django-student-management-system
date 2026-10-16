# Student Management System

A complete, beginner-friendly Django project for managing student records. It has a dashboard with statistics, full add / view / edit / delete (CRUD), search, filters, pagination and a customised Django admin. Built with Python, Django, SQLite, HTML, CSS and Bootstrap 5.

## Features

- **Dashboard** - total students, departments, courses, current-year admissions, recently added students, and distribution by department and academic year (calculated from the database). An optional Chart.js chart is shown when the library loads; the page works without it.
- **Student CRUD** - add, view, edit and delete, with a dedicated details page, a delete confirmation page, success/error messages and server-side validation.
- **Search and filters** - search by name, roll number or email; filter by department, course and academic year; all can be combined; "Clear" button. Done with the Django ORM.
- **Pagination** - Django `Paginator`, search/filter values kept across pages, invalid page numbers handled.
- **Admin** - list display, search, filters, ordering and organised fieldsets.
- **UI** - responsive, navy-blue theme, one shared `base.html` that every page extends, accessible forms and navigation.
- **63 automated tests** covering models, forms, CRUD, dashboard, search, filters, pagination, URLs and admin.

## Requirements

- Python **3.10 or newer** (tested with 3.13)
- Django **5.2 LTS** (installed from `requirements.txt`)
- An internet connection in the browser, because Bootstrap, Bootstrap Icons and Chart.js load from the jsDelivr CDN. The server itself needs no internet or extra services.

## Setup on Windows (PowerShell + VS Code)

1. **Extract** the ZIP, then in VS Code choose *File > Open Folder* and select the `student_management_system` folder. Open the terminal with *Terminal > New Terminal* (PowerShell).

2. **Create and activate a virtual environment**

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   If PowerShell says scripts are disabled, run this once, then try again:

   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
   ```

   When it works you will see `(venv)` at the start of the prompt. In VS Code, pick this interpreter with *Ctrl+Shift+P > Python: Select Interpreter*.

3. **Install dependencies**

   ```powershell
   pip install -r requirements.txt
   ```

4. **Create and apply migrations** (a first migration is already included, so `makemigrations` will say "No changes detected" - that is fine)

   ```powershell
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create an admin account** (you choose the username and password)

   ```powershell
   python manage.py createsuperuser
   ```

6. **Start the server**

   ```powershell
   python manage.py runserver
   ```

7. **Open the app**
   - Application: <http://127.0.0.1:8000/>
   - Django admin: <http://127.0.0.1:8000/admin/> (log in with the account from step 5)

Stop the server with `Ctrl+C`.

### Run the checks and tests

```powershell
python manage.py check
python manage.py test
```

## Project structure

```text
student_management_system/
├── manage.py
├── requirements.txt
├── .env.example            # placeholder settings (copy to .env if needed)
├── .gitignore
├── config/                 # project package: settings, urls, wsgi, asgi
├── templates/
│   ├── base.html           # shared layout: navbar, messages, footer
│   └── 404.html
└── students/               # the app
    ├── models.py           # Student model + validation
    ├── forms.py            # StudentForm (ModelForm) and the search/filter form
    ├── views.py            # dashboard, list, detail, create, update, delete
    ├── urls.py             # named URLs (namespace "students")
    ├── admin.py
    ├── tests.py
    ├── migrations/
    ├── templates/students/ # dashboard, list, detail, form, confirm delete (+ includes/)
    └── static/students/    # css/style.css, js/dashboard.js
```

## How to extend it

- **New student field**: add it to `Student` in `models.py`, add it to `fields` in `StudentForm` (`forms.py`), show it in the templates, then run `python manage.py makemigrations` and `python manage.py migrate`.
- **New department or course**: add a line to the `Department` or `Course` class in `models.py`, then run `makemigrations` and `migrate`.
- **Change colours**: edit the variables at the top of `students/static/students/css/style.css`.
- **Students per page**: change `STUDENTS_PER_PAGE` in `students/views.py`.

## Validation rules

- Roll number: unique (not case-sensitive), letters/numbers/hyphen/slash, saved in capitals.
- Email: valid format, unique, saved in lower case.
- Phone: 10-15 digits with an optional leading `+`.
- Date of birth and admission date cannot be in the future, and admission must be after the date of birth (also enforced by a database constraint).

## Security notes - read before putting this online

This project is a **local demo / portfolio project**. Before deploying it publicly:

1. **There is no login for the student pages.** Anyone who can open the site can view, add, edit and delete students. Only `/admin/` requires a login. Add authentication first, for example by using Django's `LoginView` and the `@login_required` decorator on the views in `students/views.py`.
2. **Set real secrets.** Create a long random `DJANGO_SECRET_KEY`, set `DJANGO_DEBUG=False`, and set `DJANGO_ALLOWED_HOSTS` to your domain. With `DJANGO_DEBUG=False` the app refuses to start if the secret key is still the development default. Use environment variables on your host; never commit a real `.env` file (it is already in `.gitignore`).
3. **Use HTTPS.** In production mode, session and CSRF cookies are marked secure. Also configure HTTPS redirects/HSTS on your host (`python manage.py check --deploy` lists what is left).
4. **Serve static files properly.** `runserver` serves them only in development. In production run `python manage.py collectstatic` and serve them with your host or a tool such as WhiteNoise.
5. **SQLite is fine for a demo**, but use a server database (such as PostgreSQL) and regular backups for real data. Student records are personal data, so protect them accordingly.
6. The CDN links in `templates/base.html` do not use Subresource Integrity hashes; add them (or host the files yourself) for a production site.

## Troubleshooting

- `python` not found: reinstall Python from python.org and tick *Add Python to PATH*, or try `py -m venv venv`.
- `No module named django`: activate the virtual environment, then run `pip install -r requirements.txt`.
- Page looks unstyled: check your internet connection (Bootstrap loads from a CDN).
- Port already in use: run `python manage.py runserver 8001`.

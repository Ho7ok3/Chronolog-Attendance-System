To run your Django system locally from GitHub, start by installing Python, Git, and pip if you haven't already. Clone your project using git clone https://github.com/Ho7ok3/Chronolog-Attendance-System.git, then navigate into the folder using cd your-repo-name. It's recommended to set up a virtual environment by running python -m venv env and activating it (env\Scripts\activate on Windows or source env/bin/activate on Mac/Linux). Next, install dependencies with pip install -r requirements.txt.

Once the packages are installed, set up the database by running python manage.py makemigrations and python manage.py migrate. If you need admin access, create a superuser using python manage.py createsuperuser. Finally, start the development server with python manage.py runserver and open the link provided (usually http://127.0.0.1:8000) in your browser to access the system.

If your project includes a .sql database file, import it manually using tools like phpMyAdmin or MySQL CLI, and make sure your database settings in settings.py are correctly configured.

-Michael Jose Alkuino
-Jasmine L. Guillena
-Michaelo Angelo Gunda

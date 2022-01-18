# Running:
1. `. venv/bin/activate`
2. `pip3 install -r requirements.txt` 
3. Run commands to load database tables and start the development server: 
   - `python3 manage.py makemigrations`
   - `python3 manage.py migrate`
   - `python3 manage.py initialize_inventory`
   - `python3 manage.py runserver 8082`
4. Navigate to <https://localhost:8082>

# Tests:
1. `. venv/bin/activate`
2. `pip3 install -r requirements.txt`
3. `python3 manage.py test`

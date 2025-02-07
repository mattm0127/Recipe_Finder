FROM python:3.10

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY db.sqlite3 db.sqlite3 

RUN python manage.py migrate

CMD ["gunicorn", "recipe_finder.wsgi:application", "--bind", "0.0.0.0:8000"]
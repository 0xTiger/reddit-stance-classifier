FROM python:3.14.4

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . /app/

CMD python3 app.py
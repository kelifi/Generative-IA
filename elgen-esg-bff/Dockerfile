FROM bitnami/python:3.10
WORKDIR /app
COPY ./configuration/ configuration/
COPY ./source/ source/
COPY ./app.py main.py
COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt
CMD python main.py
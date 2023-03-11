FROM python:3.10-slim-buster
ENV PYTHONUNBUFFERED 1

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY . /code
WORKDIR /code

ENTRYPOINT ["python", "main.py"]
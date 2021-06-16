FROM python:3.8.10
WORKDIR /app
RUN pip install pipenv
COPY Pipfile* /tmp/
RUN cd /tmp && pipenv lock --keep-outdated --requirements > requirements.txt
RUN pip install -r /tmp/requirements.txt
COPY . .
CMD ["python3", "-m", "calculator_bot"]

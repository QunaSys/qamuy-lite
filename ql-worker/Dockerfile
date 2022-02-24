FROM python:3.8

ENV POETRY_HOME=/opt/poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
RUN cd /usr/local/bin && ln -s /opt/poetry/bin/poetry
RUN poetry config virtualenvs.create false

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    # Unnecessary in runtime
    build-essential \
    git \
    openssh-client \
    curl \
    && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

RUN mkdir /root/.ssh && \
    ssh-keyscan -H github.com >> /root/.ssh/known_hosts && \
    export LC_ALL=C.UTF-8 && \
    export LANG=C.UTF-8 && \
    git config --global url."git@github.com:".insteadOf https://github.com/

COPY ./pyproject.toml ./poetry.lock /
RUN --mount=type=secret,id=SSHKEYPLUS,dst=/root/.ssh/id_rsa \
    poetry install --no-root

ENV PORT 8080
EXPOSE $PORT

COPY ./ql_worker /ql_worker

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True
ENV PRODUCTION_ENV True

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 ql_worker.main:app

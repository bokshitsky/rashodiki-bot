FROM --platform=linux/amd64 python:3.10-slim AS with-poetry

ENV PYTHONUNBUFFERED 1
WORKDIR /rashodiki

RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat gcc python3-dev && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* &&  \
    pip install poetry==1.3.1 && \
    poetry config virtualenvs.in-project true

COPY pyproject.toml /rashodiki/pyproject.toml
COPY poetry.lock /rashodiki/poetry.lock

FROM with-poetry as build
RUN poetry install --no-root --without dev

FROM with-poetry as prod
COPY alembic /rashodiki/alembic
COPY rashodiki_bot /rashodiki/rashodiki_bot
COPY --from=build /rashodiki/.venv /rashodiki/.venv

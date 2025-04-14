# Stage 1: Build
FROM python:3.13-alpine AS build

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONPATH=/app

RUN echo "TRANSCRIPTIONS: Installing dependencies" 
RUN apk update 
RUN apk add --no-install-recommends --no-cache curl build-base 
RUN rm -rf /var/cache/apk/* 
RUN curl -sSL https://install.python-poetry.org | python3 

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /transcriptions

COPY ./pyproject.toml ./poetry.lock ./

RUN echo "TRANSCRIPTIONS: Installing Poetry"  
RUN poetry config virtualenvs.create false 
RUN poetry install --no-interaction --no-root

#Stage 2: Runtime
FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONPATH=/app

WORKDIR /transcriptions

COPY . .

CMD ["poetry", "run", "uvicorn", "services.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 2: Runtime
FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONPATH=/app

WORKDIR /transcriptions

RUN apk update 
RUN apk add --no-cache curl 
RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

COPY --from=build /transcriptions/. .
COPY . .

RUN poetry install --no-interaction --no-root

CMD ["poetry", "run", "uvicorn", "services.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 1: Build
#FROM python:3.13-alpine AS build
#
#ENV PYTHONUNBUFFERED=1 \
#    PYTHONDONTWRITEBYTECODE=1 \
#    PIP_NO_CACHE_DIR=off \
#    PIP_DISABLE_PIP_VERSION_CHECK=on \
#    PIP_DEFAULT_TIMEOUT=100 \
#    PYTHONPATH=/app
#
#RUN echo "SCRAPING: Installing dependencies" 
#RUN apk update 
#RUN apk add --no-install-recommends --no-cache curl build-base python3 
#RUN rm -rf /var/cache/apk/* 
#RUN curl -sSL https://install.python-poetry.org | python3 -
#
#ENV PATH="/root/.local/bin:$PATH"
#
#WORKDIR /scraping
#
#COPY ./pyproject.toml ./poetry.lock ./
#
#RUN echo "SCRAPING: Installing Poetry" 
#RUN poetry config virtualenvs.create false 
#RUN poetry install --no-interaction --no-root
#
## Stage 2: Runtime
#FROM python:3.13-alpine
#
#ENV PYTHONUNBUFFERED=1 \
#    PYTHONDONTWRITEBYTECODE=1 \
#    PIP_NO_CACHE_DIR=off \
#    PIP_DISABLE_PIP_VERSION_CHECK=on \
#    PIP_DEFAULT_TIMEOUT=100 \
#    PYTHONPATH=/app
#
#WORKDIR /scraping
#
#RUN apk update 
#    apk add --no-cache curl 
#    curl -sSL https://install.python-poetry.org | python3 -
#
#ENV PATH="/root/.local/bin:$PATH"
#
#COPY --from=build /scraping/. .
#COPY . .
#RUN poetry install --no-interaction --no-root
#
#CMD ["poetry", "run", "uvicorn", "services.main:app", "--host", "0.0.0.0", "--port", "8000"]
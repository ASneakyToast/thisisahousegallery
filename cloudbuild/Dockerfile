
#######################################
FROM node:20-alpine AS client-builder

ARG APP_HOME=/app
WORKDIR ${APP_HOME}

# Install FE dependencies
COPY package.json ${APP_HOME}
RUN npm install --loglevel verbose && npm cache clean --force

# Copy project files into the docker image
COPY . ${APP_HOME}

# Build FE
RUN npm run build


#######################################
# define an alias for the specific python version used in this file.
FROM docker.io/python:3.9.12-slim-bullseye AS python

# Python build stage
FROM python AS python-build-stage

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  # psycopg dependencies
  libpq-dev

# Requirements are installed here to ensure they will be cached.
COPY ./requirements .

# Create Python Dependency and Sub-Dependency Wheels.
RUN pip wheel --wheel-dir /usr/src/app/wheels  \
  -r prod.txt


#######################################
# Python 'run' stage
FROM python AS python-run-stage

ARG APP_HOME=/app

# Removes output stream buffering, allowing for more efficient logging
# i.e. print stmt output to sys.stdout immediately (without flush)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

####ENV PYTHONPATH "${PYTHONPATH}:${APP_HOME}/"
#----------------
ARG django_settings
ENV DJANGO_SETTINGS_MODULE="${django_settings}"
ARG build_type
ENV BUILD_TYPE="${build_type}"
ARG cloud_project
ENV GCP_PROJECT="${cloud_project}"
RUN echo "${DJANGO_SETTINGS_MODULE} - ${BUILD_TYPE} - ${GCP_PROJECT}"
#----------------

WORKDIR ${APP_HOME}

RUN addgroup --system django \
    && adduser --system --ingroup django django


# Install required system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
  # psycopg dependencies
  libpq-dev \
  # Translations dependencies
  gettext \
  # entrypoint
  wait-for-it \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*


# All absolute dir copies ignore workdir instruction. All relative dir copies are wrt to the workdir instruction
# copy python dependency wheels from python-build-stage
COPY --from=python-build-stage /usr/src/app/wheels  /wheels/

# use wheels to install python dependencies
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
  && rm -rf /wheels/


COPY --chown=django:django ./cloudbuild/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY --chown=django:django ./cloudbuild/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start


# copy application code to WORKDIR
COPY --from=client-builder --chown=django:django ${APP_HOME} ${APP_HOME}


RUN chown -R django:django ${APP_HOME}

USER django

ENTRYPOINT ["/entrypoint"]

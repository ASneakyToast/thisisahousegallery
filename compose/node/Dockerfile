FROM docker.io/node:22.12-bookworm-slim

WORKDIR /app

COPY ./package.json /app

RUN npm install --loglevel verbose && npm cache clean --force

ENV PATH=./node_modules/.bin/:$PATH

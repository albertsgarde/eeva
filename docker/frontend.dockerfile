FROM node:18.19-alpine3.19 AS frontend-build
WORKDIR /identity
COPY ./interview-frontend/package.json ./interview-frontend/package-lock.json ./
RUN npm install --frozen-lockfile

COPY ./interview-frontend/ .
RUN npm run build

FROM node:18.19-alpine3.19 AS frontend-prod
WORKDIR /identity
COPY --from=frontend-build /identity/ ./

ENV BACKEND_ORIGIN=http://localhost:8000

CMD PUBLIC_BACKEND_ORIGIN=${BACKEND_ORIGIN} node build

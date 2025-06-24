FROM node:22.16.0-alpine3.22 AS frontend-build
WORKDIR /eeva
COPY ./interview-frontend/package.json ./interview-frontend/package-lock.json ./
RUN npm install --frozen-lockfile

COPY ./interview-frontend/ .
RUN npm run build

FROM node:22.16.0-alpine3.22 AS frontend-prod
WORKDIR /eeva
COPY --from=frontend-build /eeva/ ./

ENV BACKEND_ORIGIN=http://localhost:8000

CMD PUBLIC_BACKEND_ORIGIN=${BACKEND_ORIGIN} node build

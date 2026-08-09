FROM node:22-slim AS frontend-build

WORKDIR /frontend

COPY ["ATLAS - FRONT_END/package.json", "ATLAS - FRONT_END/package-lock.json", "./"]
RUN npm ci

COPY ["ATLAS - FRONT_END/", "./"]
ARG VITE_ATLAS_API_KEY=atlas-mvp-2026
ARG VITE_ATLAS_API_BASE_URL=
ENV VITE_ATLAS_API_KEY=$VITE_ATLAS_API_KEY
ENV VITE_ATLAS_API_BASE_URL=$VITE_ATLAS_API_BASE_URL
RUN npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY ["ATLAS VENCIMENTOS/requirements.txt", "."]
RUN pip install --no-cache-dir -r requirements.txt

COPY ["ATLAS VENCIMENTOS/", "./"]
COPY --from=frontend-build /frontend/dist /app/frontend_dist
RUN mkdir -p /app/staticfiles

ENV FRONTEND_DIST_DIR=/app/frontend_dist

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

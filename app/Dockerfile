FROM python:3.12-alpine

WORKDIR /app
COPY main.py .

# Set by the CI pipeline to the git commit, shown on the page
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Run as a non-root user
USER 10001
EXPOSE 8080

HEALTHCHECK CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1
CMD ["python", "main.py"]

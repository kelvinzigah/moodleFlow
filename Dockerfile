FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN addgroup --system schoolassistant \
    && adduser --system --ingroup schoolassistant schoolassistant

COPY . .
RUN python -m pip install --no-cache-dir . \
    && chown -R schoolassistant:schoolassistant /app

USER schoolassistant

CMD ["python", "-m", "school_assistant_worker.main"]

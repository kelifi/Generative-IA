# Bit nami builder
FROM bitnami/python:3.8.11 as builder
ENV PATH="/app/.venv/bin:${PATH}"
WORKDIR /app

RUN python -m venv .venv

COPY requirements.txt /app
RUN  python3 -m pip install -r requirements.txt

COPY . /app

# The production image is constructed with a smaller, production grade
# base image, and your code built in the previous build stage.
FROM bitnami/python:3.8.11-prod
RUN apt-get update && pip install --upgrade pip && apt-get install libsndfile1 -y && apt install ffmpeg -y
ENV PATH="/app/.venv/bin:${PATH}"
WORKDIR /app

COPY --from=builder /app /app
RUN mkdir files
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM python:3.10 as builder
ENV PATH="/app/.venv/bin:${PATH}"

WORKDIR /app
RUN python -m venv .venv
RUN /app/.venv/bin/python3 -m pip install --upgrade --no-cache-dir pip

COPY ./requirements.txt /app
RUN python3 -m pip install --no-cache-dir -r requirements.txt
COPY . /app

FROM builder as tester
RUN python3 -m pip install --no-cache-dir coverage pytest-cov pytest pylint bandit
ENTRYPOINT coverage run -m pytest --junitxml=reports/pytest-report.xml --continue-on-collection-errors tests/ && \
    coverage xml -o reports/coverage.xml && \
    pylint cases --exit-zero -rn --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" --output-format=parseable > reports/pylint-report.xml

FROM builder as app
CMD python main.py
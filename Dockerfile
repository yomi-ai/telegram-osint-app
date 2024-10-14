FROM python:3.10

WORKDIR /app


RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install pip==24.0

COPY . /app

RUN pip install -r requirements.txt

CMD ["uvicorn", "src.app_module:http_server", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
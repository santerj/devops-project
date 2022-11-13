FROM python:3.10-slim
WORKDIR /app
COPY imed/src/* /app/
COPY ../common.py /app/
RUN python -m pip install --upgrade pip -r requirements.txt
CMD ["python", "app.py"]

FROM python:3.10-slim
WORKDIR /app
COPY src/* /app
RUN python -m pip install --upgrade pip -r requirements.txt
CMD ["python", "app.py"]
EXPOSE 80

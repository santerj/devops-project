FROM python:3.10-slim
WORKDIR /app
COPY api-gw/src/* /app/
COPY ../common.py /app/
RUN python -m pip install --upgrade pip -r requirements.txt
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=8083"]
EXPOSE 8083

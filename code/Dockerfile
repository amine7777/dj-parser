
FROM python:3.13-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir \
    -r requirements.txt

EXPOSE 7860
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
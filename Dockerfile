FROM python:3.10
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN python init_db.py
CMD ["python", "run.py"]

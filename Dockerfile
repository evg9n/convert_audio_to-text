FROM python:3.10.12-alpine

WORKDIR /app

RUN python -m pip install --upgrade pip

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
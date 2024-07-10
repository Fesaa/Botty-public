FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apk add git enchant2 hunspell-en
RUN pip install -r requirements.txt
RUN mkdir _logs

COPY . .

ENV PYENCHANT_LIBRARY_PATH=/usr/lib/enchant-2/enchant_hunspell.so

CMD ["python", "main.py"]


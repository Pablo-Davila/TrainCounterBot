FROM python:3.14-slim

WORKDIR /code

RUN mkdir /data
VOLUME [ "/data" ]

ADD ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ADD ./src/* .

CMD [ "python3", "train_counter_bot.py" ]

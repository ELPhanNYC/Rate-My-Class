FROM python

WORKDIR /app

COPY . .

RUN pip3 install -r requirements.txt

EXPOSE 8080 27017

CMD python3 -u server.py
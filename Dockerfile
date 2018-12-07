FROM python:3.6

RUN mkdir /app
COPY ./beta-issues /app
WORKDIR /app

#RUN apk update \
#    && apk upgrade \
#    && apk add --update gcc libc-dev libxml2-dev libxslt-dev\
#    && pip install -r requirements.txt

RUN pip install -r requirements.txt
# && apk add --update alpine-sdk gcc g++ libc-dev libxml2-dev libxslt-dev libxslt-dev==1.1.29-r0\

ENV FLASK_APP __init__.py
ENV FLASK_DEBUG 1

EXPOSE 5001
ENTRYPOINT ["gunicorn", "-b", ":5001", "__init__:app"]

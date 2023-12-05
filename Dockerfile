FROM python:3.12-slim

RUN apt-get update && apt-get install -y git
COPY org.eclipse.lemminx-uber /usr/local/bin/lemminx
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY format.py /format.py

ENTRYPOINT [ "python3", "/format.py" ]

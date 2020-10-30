FROM python:3.8-slim

LABEL maintainer=francoisancel@gmail.com
RUN apt-get update && apt-get install -y gcc python3 python3-pip

RUN useradd --create-home --shell /bin/bash appuser
USER appuser
ENV PATH="/home/appuser/.local/bin:${PATH}"
RUN mkdir /home/appuser/src && mkdir /home/appuser/db

COPY requirement.txt /home/appuser/src
WORKDIR /home/appuser/src
EXPOSE 5000

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -U -r requirement.txt

COPY main.py /home/appuser/src
CMD ["python", "main.py"]
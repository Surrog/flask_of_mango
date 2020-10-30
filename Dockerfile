FROM python:latest

LABEL maintainer=francoisancel@gmail.com
RUN apt-get update && apt-get install -y gcc mongodb python3
RUN systemctl enable mongod --now

RUN useradd --create-home --shell /bin/bash appuser
USER appuser
ENV PATH="home/appuser/.local/bin:${PATH}"
RUN mkdir /home/appuser/src && mkdir /home/appuser/static && mkdir /home/appuser/db

COPY main.py /home/appuser/src
COPY Pipfile /home/appuser/src
WORKDIR /home/appuser/src

RUN python -m pip install --upgrade pip
RUN pip install -p

CMD ["python", "main.py"]
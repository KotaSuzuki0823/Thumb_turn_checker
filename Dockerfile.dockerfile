FROM python:3.7-slim-buster as runner
ENV PYTHONUNBUFFERED=0
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopencv-dev \
    python3-pip \
    python3-setuptools \
    && mkdir /code \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code
ADD requirements.txt /code

RUN pip3 install -r requirements.txt

CMD [ "python3" , "line.py"]
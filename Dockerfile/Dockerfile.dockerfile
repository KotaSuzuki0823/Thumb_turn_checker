FROM ubuntu:18.04
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=0
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopencv-dev \
    python3 \
    python3-pip \
    python3-setuptools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN mkdir /code
WORKDIR /code
ADD . /code/

RUN python3 -m pip install -r requirements.txt
FROM python:3.7-slim-buster as runner
ENV PYTHONUNBUFFERED=0
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopencv-dev \
    python3-pip \
    python3-setuptools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /code

RUN python3 -m pip install -r requirements.txt

CMD [ "python3" , "line.py"]
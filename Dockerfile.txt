FROM pkjmesra/ta-lib-debian_gnu_linux:latest as base-image
ENV PYTHONUNBUFFERED 1

FROM scratch

COPY --from=base-image ["/", "/"]

RUN apt-get -y install libc-dev
RUN apt-get update && apt-get -y install build-essential

WORKDIR /

RUN apt-get -y install unzip

RUN wget https://github.com/pkjmesra/pkscreener/archive/main.zip && \
  unzip main.zip && \
  rm -rf main.zip

WORKDIR pkscreener-main
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

WORKDIR /
RUN cd src

RUN python3 ./pkscreener


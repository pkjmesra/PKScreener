FROM pkjmesra/ta-lib-debian_gnu_linux:latest as base-image
ENV PYTHONUNBUFFERED 1

FROM scratch

COPY --from=base-image ["/", "/"]

RUN apt-get -y install libc-dev
RUN apt-get update && apt-get -y install build-essential

WORKDIR /

RUN apt-get -y install unzip

RUN wget https://github.com/pkjmesra/nseta/archive/main.zip && \
  unzip main.zip && \
  rm -rf main.zip

WORKDIR nseta-main
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN python3 setup.py clean build install

WORKDIR /
RUN rm -rf nseta*

RUN python3 -c 'import numpy, talib; close = numpy.random.random(100); output = talib.SMA(close); print(output)'

RUN python3 -c "import nseta; print(nseta.__version__);"

RUN python3 -c "from nseta.scanner.volumeScanner import volumeScanner; from nseta.scanner.baseStockScanner import ScannerType; s=volumeScanner(ScannerType.Volume,['HDFC']); s.scan();"

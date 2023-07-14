FROM python:3.9.3 as python-builder
ENV PYTHONUNBUFFERED 1
ENV PYTHON_TA_LIB_VERSION 0.4.19

# TA-Lib
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
  tar -xvzf ta-lib-0.4.0-src.tar.gz && \
  cd ta-lib/ && \
  ./configure --prefix=/usr && \
  make && \
  make install && \
  pip3 install setuptools numpy

RUN rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
RUN pip3 install ta-lib==${PYTHON_TA_LIB_VERSION}

CMD ["python3"]

RUN python3 -c 'import numpy, talib; close = numpy.random.random(100); output = talib.SMA(close); print(output)'
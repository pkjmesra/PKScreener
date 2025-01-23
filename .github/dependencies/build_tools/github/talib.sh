#!/bin/bash
echo ""
echo "[+] Starting TA-Lib installation, Please Wait..."
sleep 1
echo "[+] This may take some time as per your Internet Speed, Please Wait..."

wget https://raw.githubusercontent.com/pkjmesra/PKScreener/main/.github/dependencies/ta-lib-0.6.4-src.tar.gz && \
  tar -xzf ta-lib-0.6.4-src.tar.gz && \
  cd ta-lib-0.6.4/ && \
  wget 'http://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.guess;hb=HEAD' -O config.guess && \
  wget 'http://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.sub;hb=HEAD' -O config.sub && \
  ./configure --prefix=/usr && \
  make && \
  make install
pip3 install ta-lib

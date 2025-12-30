# """
#     The MIT License (MIT)

#     Copyright (c) 2023 pkjmesra

#     Permission is hereby granted, free of charge, to any person obtaining a copy
#     of this software and associated documentation files (the "Software"), to deal
#     in the Software without restriction, including without limitation the rights
#     to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#     copies of the Software, and to permit persons to whom the Software is
#     furnished to do so, subject to the following conditions:

#     The above copyright notice and this permission notice shall be included in all
#     copies or substantial portions of the Software.

#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#     IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#     FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#     AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#     LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#     OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#     SOFTWARE.

# """
# docker buildx build --push --platform linux/arm/v7,linux/arm64/v8,linux/amd64 --tag pkjmesra/pkscreener:latest .
# docker buildx build --load --platform linux/arm64/v8,linux/amd64 --tag pkjmesra/pkscreener:latest . --no-cache
# docker buildx build --push --platform linux/arm64/v8,linux/amd64 --tag pkjmesra/pkscreener:latest . --no-cache

FROM pkjmesra/pkscreener:base AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /
RUN rm -rf /PKScreener-main main.zip* && \
    curl -JL https://github.com/pkjmesra/PKScreener/archive/refs/heads/main.zip -o main.zip && \
    unzip main.zip && \
    rm -rf main.zip*
WORKDIR /PKScreener-main
COPY requirements.txt .

# Install libsql FIRST based on architecture using pre-built wheels
# This prevents pip from trying to build libsql from source on ARM
RUN ARCH=$(uname -m) && \
    echo "Installing libsql for architecture: $ARCH" && \
    if [ "$ARCH" = "x86_64" ]; then \
        pip3 install https://github.com/pkjmesra/libsql-python/releases/download/released/libsql-0.1.6-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl || echo "libsql x86_64 wheel not found, will use SQLite fallback"; \
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then \
        pip3 install https://github.com/pkjmesra/libsql-python/releases/download/released/libsql-0.1.6-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl || echo "libsql ARM wheel not found, will use SQLite fallback"; \
    else \
        echo "libsql not available for architecture: $ARCH, using SQLite fallback"; \
    fi

# Install requirements, excluding libsql since we handled it above
# The --no-deps on pkbrokers prevents re-installing libsql
RUN pip3 install --upgrade pip && \
    pip3 uninstall pkscreener PKNSETools PKDevTools pkbrokers -y || true && \
    grep -v "^libsql" requirements.txt > requirements_no_libsql.txt || cp requirements.txt requirements_no_libsql.txt && \
    pip3 install --no-cache-dir -r requirements_no_libsql.txt && \
    pip3 install . && \
    mv /PKScreener-main/pkscreener/pkscreenercli.py /pkscreenercli.py && \
    rm -rf /PKScreener-main && \
    mkdir -p /PKScreener-main/pkscreener/ && \
    mv /pkscreenercli.py /PKScreener-main/pkscreener/pkscreenercli.py

ENV TERM=xterm
COPY cve-fixes.txt .
RUN pip3 install -r cve-fixes.txt
ENV PKSCREENER_DOCKER=1
ENTRYPOINT ["python3","pkscreener/pkscreenercli.py"]
# Run with 
# docker run -it pkjmesra/pkscreener:latest

FROM debian:bullseye-slim AS builder
ARG TARGETARCH
ARG TARGETVARIANT

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache-1-$TARGETARCH$TARGETVARIANT-builder,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,id=apt-cache-2-$TARGETARCH$TARGETVARIANT-builder,sharing=locked \
    <<EOS
set -ex
rm -f /etc/apt/apt.conf.d/docker-clean
echo 'Binary::apt::APT::Keep-Downloaded-Packages "1";' > /etc/apt/apt.conf.d/keep-cache
echo 'APT::Install-Recommends "0";' > /etc/apt/apt.conf.d/no-recommends
echo 'APT::AutoRemove::RecommendsImportant "0";' >> /etc/apt/apt.conf.d/no-recommends
apt-get update
apt-get install -y libtool make cmake libseccomp-dev gcc python3 python3-venv
EOS

COPY Judger/ /app/
RUN <<EOS
set -ex
mkdir /app/build
cmake -S . -B build
cmake --build build --parallel $(nproc)
EOS

RUN <<EOS
set -ex
cd bindings/Python
python3 -m venv .venv
.venv/bin/pip3 install build
.venv/bin/python3 -m build -w
EOS

FROM debian:bullseye-slim
ARG TARGETARCH
ARG TARGETVARIANT

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN --mount=type=cache,target=/var/cache/apt,id=apt-cache-1-$TARGETARCH$TARGETVARIANT-final,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,id=apt-cache-2-$TARGETARCH$TARGETVARIANT-final,sharing=locked \
    <<EOS
set -ex
rm -f /etc/apt/apt.conf.d/docker-clean
echo 'Binary::apt::APT::Keep-Downloaded-Packages "1";' > /etc/apt/apt.conf.d/keep-cache
echo 'APT::Install-Recommends "0";' > /etc/apt/apt.conf.d/no-recommends
echo 'APT::AutoRemove::RecommendsImportant "0";' >> /etc/apt/apt.conf.d/no-recommends
needed="python3-minimal \
    python3-venv \
    libpython3-stdlib \
    libpython3-dev \
    golang-go \
    openjdk-11-jdk \
    gcc \
    g++ \
    nodejs \
    strace \
    curl"  
savedAptMark="$(apt-mark showmanual) $needed"
apt-get update
apt-get install -y ca-certificates curl gnupg wget
mkdir -p /etc/apt/keyrings
wget -qO- https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor -o /etc/apt/keyrings/adoptium.gpg
echo "deb [signed-by=/etc/apt/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb bullseye main" > /etc/apt/sources.list.d/adoptium.list
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_16.x bullseye main" > /etc/apt/sources.list.d/nodesource.list
apt-get update
apt-get install -y $needed
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 9
rm -rf /usr/lib/jvm/temurin-11-jdk-*/jmods
rm -rf /usr/lib/jvm/temurin-11-jdk-*/lib/src.zip
apt-mark auto '.*' > /dev/null
apt-mark manual $savedAptMark
apt-get purge -y --auto-remove
EOS

COPY --from=builder --chmod=755 --link /app/build/libjudger.so /usr/lib/judger/libjudger.so
COPY --from=builder /app/bindings/Python/dist/ /app/
RUN --mount=type=cache,target=/root/.cache/pip,id=pip-cache-$TARGETARCH$TARGETVARIANT-final \
    <<EOS
set -ex
python3 -m venv .venv
CC=gcc .venv/bin/pip3 install --compile --no-cache-dir flask gunicorn idna psutil requests
.venv/bin/pip3 install *.whl
EOS

COPY server/ /app/
RUN <<EOS
set -ex
chmod -R u=rwX,go=rX /app/
chmod +x /app/entrypoint.sh
gcc -shared -fPIC -o unbuffer.so unbuffer.c
useradd -u 901 -r -s /sbin/nologin -M compiler
useradd -u 902 -r -s /sbin/nologin -M code
useradd -u 903 -r -s /sbin/nologin -M -G code spj
mkdir -p /usr/lib/judger
EOS

RUN <<EOS
set -ex
gcc --version
g++ --version
python3 --version
java -version
node --version
EOS

HEALTHCHECK --interval=5s CMD [ "/app/.venv/bin/python3", "/app/service.py" ]
EXPOSE 8080
ENTRYPOINT [ "/app/entrypoint.sh" ]
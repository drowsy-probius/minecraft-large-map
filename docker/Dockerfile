FROM ubuntu:24.04

RUN mkdir /data \
    && apt update \
    && apt upgrade -y \
    && apt install -y curl

RUN curl https://www.worldpainter.net/files/worldpainter_2.22.1.deb -o worldpainter.deb \
    && apt install -y ./worldpainter.deb \
    && rm worldpainter.deb \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

# ENTRYPOINT [ "wpscript" ]
CMD [ "wpscript" ]

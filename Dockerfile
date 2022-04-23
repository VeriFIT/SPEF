FROM alpine:3.14
RUN adduser -D -u 1000 test || useradd -u 1000 test

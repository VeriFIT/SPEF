FROM alpine:3.14
RUN adduser -D -u 1000 -G 1000 test || useradd -u 1000 -g 1000 test

# FROM centos:7
# RUN yum install -y file strace

FROM fedora:28
RUN addgroup -g 1001 test || groupadd -g 1001 test
RUN adduser -D -u 1000 -G test test || useradd -u 1000 -g test test
RUN yum install -y file strace bc
USER test
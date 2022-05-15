echo """FROM fedora:34
RUN addgroup -g 1001 test 2>/dev/null || groupadd -g 1001 test
RUN adduser -D -u 1000 -G test test 2>/dev/null || useradd -u 1000 -g test test
RUN yum install -y file strace bc
USER test
""" >> Dockerfile
docker build -f Dockerfile -t test .

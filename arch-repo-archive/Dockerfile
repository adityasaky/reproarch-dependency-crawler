FROM archlinux:latest

LABEL maintainer="Santiago Torres-Arias <santiago@archlinux.org>"

RUN pacman -Syyu --noconfirm python python-xtarfile

# this script obtains a database file with the dependent packages
COPY dependency-report.py /

COPY entrypoint.sh /

ENTRYPOINT /entrypoint.sh

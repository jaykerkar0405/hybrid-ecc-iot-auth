#!/bin/bash
set -eux
fallocate -l 1G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
dnf install -y python3.11 python3.11-pip tar
touch /var/tmp/provision-done

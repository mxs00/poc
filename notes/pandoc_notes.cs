

sudo docker commit 86d3652eb066 quay.io/sarframx01/pdoc
sudo docker push quay.io/sarframx01/pdoc



docker pull quay.io/sarframx01/pdoc:latest





//---------- raw docker file
# Use Red Hat UBI9 Python 3.12 as base image
FROM registry.access.redhat.com/ubi9/python-312:9.6-1756995774 AS builder

WORKDIR /app

COPY ./nltk_data ./nltk_data 

# Use Red Hat UBI9 Python 3.12 as base image
FROM builder AS stage2

# Switch to root for installation
USER root

# Install dependencies
RUN dnf install -y wget tar gzip && dnf clean all

# Define the Pandoc tarball URL
#ARG PANDOC_URL=https://github.com/jgm/pandoc/releases/download/3.3/pandoc-3.3-linux-amd64.tar.gz
ARG PANDOC_URL=https://github.com/jgm/pandoc/releases/download/3.8.2.1/pandoc-3.8.2.1-linux-amd64.tar.gz

# Download and install Pandoc manually
RUN wget ${PANDOC_URL} -O /tmp/pandoc.tar.gz && \
    tar -xzf /tmp/pandoc.tar.gz -C /opt && \
    ln -s /opt/pandoc-3.8.2.1/bin/pandoc /usr/local/bin/pandoc && \
    rm /tmp/pandoc.tar.gz

# Verify Pandoc installation
RUN pandoc --version





//old file
# Use Red Hat UBI9 Python 3.12 as base image
FROM registry.access.redhat.com/ubi9/python-312:9.6-1749631862

# Switch to root for installation
USER root

# Install dependencies
RUN dnf install -y wget tar gzip && dnf clean all

# Define the Pandoc tarball URL
ARG PANDOC_URL=https://github.com/jgm/pandoc/releases/download/3.3/pandoc-3.3-linux-amd64.tar.gz

# Download and install Pandoc manually
RUN wget ${PANDOC_URL} -O /tmp/pandoc.tar.gz && \
    tar -xzf /tmp/pandoc.tar.gz -C /opt && \
    ln -s /opt/pandoc-3.3/bin/pandoc /usr/local/bin/pandoc && \
    rm /tmp/pandoc.tar.gz

# Verify Pandoc installation
RUN pandoc --version

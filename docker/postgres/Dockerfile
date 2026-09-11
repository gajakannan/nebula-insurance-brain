# PostgreSQL 18 with pgvector and Apache AGE, pinned per docker/DEPENDENCY-MATRIX.md.
# btree_gist ships with the base image's contrib and only needs CREATE EXTENSION.
#
# AGE fallback (F0001-S0002 edge case): if the AGE build fails against 18.x, pin
# FROM postgres:17.x here instead and record the outcome + failure text in
# docker/DEPENDENCY-MATRIX.md. Never downgrade silently.
FROM postgres:18.0-trixie

# renovate: datasource=github-releases depName=pgvector/pgvector
ARG PGVECTOR_VERSION=v0.8.6
# renovate: datasource=github-releases depName=apache/age
ARG AGE_VERSION=PG18/v1.8.0-rc0

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        build-essential \
        git \
        postgresql-server-dev-18 \
        flex \
        bison \
    && update-ca-certificates \
    && git clone --branch "${PGVECTOR_VERSION}" --depth 1 https://github.com/pgvector/pgvector.git /tmp/pgvector \
    && make -C /tmp/pgvector OPTFLAGS="" \
    && make -C /tmp/pgvector install \
    && git clone --branch "${AGE_VERSION}" --depth 1 https://github.com/apache/age.git /tmp/age \
    && make -C /tmp/age install \
    && rm -rf /tmp/pgvector /tmp/age \
    && apt-get purge -y --auto-remove build-essential git flex bison \
    && rm -rf /var/lib/apt/lists/*

COPY init/ /docker-entrypoint-initdb.d/

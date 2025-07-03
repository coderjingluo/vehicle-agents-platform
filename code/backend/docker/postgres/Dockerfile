FROM postgres:15

LABEL maintainer="KunlunSec AI Platform <admin@kunlunsec.com>"

# Configuration
ENV POSTGRES_DB=automotive_security
ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=admin123
ENV POSTGRES_INITDB_ARGS="--encoding=UTF-8 --locale=en_US.utf8"
ENV PGDATA=/var/lib/postgresql/data/pgdata

# Custom configuration
COPY postgresql.conf /etc/postgresql/postgresql.conf
COPY pg_hba.conf /etc/postgresql/pg_hba.conf

# Initialize scripts
COPY init.sql /docker-entrypoint-initdb.d/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD pg_isready -U admin -d automotive_security || exit 1

# Default port
EXPOSE 5432

# Set the default command
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"] 
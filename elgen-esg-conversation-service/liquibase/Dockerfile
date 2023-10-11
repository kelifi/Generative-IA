FROM liquibase/liquibase:4.23.0

# Download the Postgres driver and move it to the liquibase lib directory
RUN mkdir /liquibase/drivers
RUN curl -o /liquibase/drivers/postgresql.jar https://jdbc.postgresql.org/download/postgresql-42.5.4.jar



COPY /changelogs/* /liquibase/
COPY liquibase.properties /liquibase

CMD ["sh", "-c", "liquibase update --url=jdbc:postgresql://${DB_HOST}:${DB_PORT}/${DB_NAME} --username=${DB_USER} --password=${DB_PASSWORD} --defaultsFile=liquibase.properties"]

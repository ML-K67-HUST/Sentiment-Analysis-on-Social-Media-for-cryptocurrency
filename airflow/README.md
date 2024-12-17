```
docker build . --tag sentiman_airflow:0.1
docker network create sentiman-network
docker exec -it sentiman-airflow-postgres psql -U postgres
CREATE ROLE "sentiman-staging" WITH LOGIN PASSWORD 'postgres';
ALTER ROLE "sentiman-staging" CREATEDB;
\q
docker-compose up airflow-init
docker-compose up -d
```
CREATE USER postgres WITH PASSWORD 'postgres_user';
CREATE DATABASE postgres;
GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
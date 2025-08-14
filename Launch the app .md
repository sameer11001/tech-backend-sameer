--Initialize Alembic
alembic init migrations

-- Generate Migration
alembic revision --autogenerate -m "update the tabless"

-- Apply Migration
alembic upgrade head

-- Stamp Head
alembic stamp head

and need to create procedure and UUID7 from the db file in postgres

\*\*\* this is in redis client
CONFIG SET notify-keyspace-events KxE
CONFIG GET notify-keyspace-events

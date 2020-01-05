#!/bin/bash

if [  -z "${1}"  -o  -z "${2}"  ]
then
    echo "Usage: ${0} <quest.csv> <answer.csv>"
    exit -1
fi

QUESTS=$(realpath "${1}")
ANSWERS=$(realpath "${2}")


DUMPFILE="dumps/$(date +%F_%H:%M:%S).sql"
mkdir -p "dumps"
pg_dump --host=127.0.0.1 -U lector OStest > "${DUMPFILE}"

psql -1 --host=127.0.0.1 -U lector OStest <<EOF
DROP TABLE IF EXISTS student;
DROP TABLE IF EXISTS quests;
DROP TABLE IF EXISTS truth;
DROP TABLE IF EXISTS results;

-- Тут мы просто хохраняем информацию о сутденте
CREATE TABLE IF NOT EXISTS student(name TEXT, grp TEXT, ctime TIMESTAMP, PRIMARY KEY(name,grp));

-- Тут будут храниться все вопросы, которые будут заданы
CREATE TABLE IF NOT EXISTS quests(id TEXT PRIMARY KEY, quest JSON);
COPY quests FROM '${QUESTS}' CSV DELIMITER ',' QUOTE '"' HEADER FREEZE;

-- Тут будем хратить ответы
CREATE TABLE IF NOT EXISTS truth(quest TEXT PRIMARY KEY, salt TEXT, hash TEXT);
COPY truth FROM '${ANSWERS}' CSV DELIMITER ',' QUOTE '"' HEADER FREEZE;

CREATE TABLE IF NOT EXISTS results(student TEXT, quest TEXT, answer TEXT DEFAULT(''), start TIMESTAMP DEFAULT('2000-01-01'), stop TIMESTAMP DEFAULT('2000-01-01'));
EOF


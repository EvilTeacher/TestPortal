DROP TABLE student;
DROP TABLE quests;
DROP TABLE results;


-- Тут мы просто хохраняем информацию о сутденте
CREATE TABLE IF NOT EXISTS student(name TEXT, grp TEXT, ctime TIMESTAMP, PRIMARY KEY(name,grp));

-- Тут будут храниться все вопросы с вариантами ответов,
-- которые могут быть заданы 
CREATE TABLE IF NOT EXISTS quests(id SERIAL PRIMARY KEY, quest TEXT, answer1 TEXT, answer2 TEXT, answer3 TEXT, answer4 TEXT);

-- Тут формируется пул для будующих ответов студента, а потом
-- он фиксируется
CREATE TABLE IF NOT EXISTS results(student TEXT, quest INT, answer TEXT DEFAULT(''), start TIMESTAMP DEFAULT('2000-01-01'), stop TIMESTAMP DEFAULT('2000-01-01'));

#!/usr/bin/python3
# -*- coding: utf-8 -*-

#from sys import argv, stderr

#from app import app
import sys
import glob
import json
import random
import psycopg2 as db


db_config = {'dbname':'OStest',
             'user':'lector',
             'password':'123',
             'host':'localhost'}
to_db = []
for name in glob.glob("quests/*.json"):
    allitem = json.load(open(name,'r'))
    for item in allitem:
        questions = item['quests']
        while len(questions) > 0:
            q = random.choice(questions)
            questions.remove(q)
            answ1 = list(item['answer1'])
            while len(answ1) > 0 :
                a1 = random.choice(answ1)
                answ1.remove(a1)
                answ2 = list(item['answer2'])
                while len(answ2) > 0 :
                    a2 = random.choice(answ2)
                    answ2.remove(a2)
                    answ3 = list(item['answer3'])
                    while len(answ3) > 0 :
                        a3 = random.choice(answ3)
                        answ3.remove(a3)
                        answ4 = list(item['answer4'])
                        while len(answ4) > 0 :
                            a4 = random.choice(answ4)
                            answ4.remove(a4)
                            to_db.append({'q':q,'a1':a1,
                                          'a2':a2,'a3':a3,'a4':a4})

with db.connect(**db_config) as conn:
    sql = conn.cursor()
    for quest in to_db:
        sql.execute("INSERT INTO quests(quest, answer1, "+
                    "answer2, answer3, answer4) VALUES(%(q)s,"+
                    "%(a1)s,%(a2)s,%(a3)s,%(a4)s)", quest)
    conn.commit()

#!/usr/bin/python3
# -*- coding: utf-8 -*-

#from sys import argv, stderr

#from app import app
import sys
import glob
import json
import random
import psycopg2 as db
import hashlib
import csv


db_config = {'dbname':'OStest', 'user':'lector',
             'password':'123', 'host':'localhost'}
fieldnames = ['Group','Name','Time','Result']

fd = open('result.csv', "w")
writer = csv.DictWriter(fd, delimiter=';',
                        fieldnames=fieldnames,
                        quotechar='"',
                        quoting=csv.QUOTE_ALL)
writer.writeheader()

with db.connect(**db_config) as conn:
    sql = conn.cursor()
    sql.execute("SELECT name, grp, ctime, (name||grp) as sid"+
                " FROM student GROUP BY name, ctime, grp, "+
                "sid ORDER BY grp, name, ctime;")

    for name, grp, ctime, sid in sql.fetchall():
        sid = hashlib.sha1(sid.encode('utf-8')).hexdigest()    
        sql.execute("SELECT quest||'_'||answer FROM results "+
                    "WHERE student = %(sid)s AND "+
                    "((stop - start) < interval '31 second')",
                    {'sid':sid})
        
        anwer = set([row[0] for row in sql.fetchall()])
        if len(anwer) == 0 : continue
        sql.execute("SELECT id, answer1 FROM quests WHERE id "+
                    "in (SELECT quest FROM results WHERE "+
                    "student = %(sid)s)", {'sid':sid})
        true = set(["%d_%s" % (row[0],hashlib.sha1(
            row[1].encode('utf-8')).hexdigest())
                    for row in sql.fetchall()])
        result = float(float(len(set(anwer & true))) /
                       float(len(true)))        
        writer.writerow({'Group':grp,'Name':name,
                         'Time':ctime,'Result':result})

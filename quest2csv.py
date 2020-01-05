#!/usr/bin/python3
# -*- coding: utf-8 -*-

from sys import argv
import json
import csv
from hashlib import md5
from getpass import getpass
import random

if len(argv) != 4:
    print("Usage: " + argv[0] + "<quest.json> <quest.csv> <answer.csv>")
    exit(-1)

shadow = md5(getpass().encode('utf-8')).hexdigest()
toSalt = ['%c' % ch for ch in range(ord(' '),ord('~'))]
quests = csv.DictWriter(open(argv[2],'w'),
                       fieldnames=['ID','QUEST'])
answers = csv.DictWriter(open(argv[3],'w'),
                        fieldnames=['QUEST','SALT','HASH'])

quests.writeheader()
answers.writeheader()

for item in json.load(open(argv[1],'r')):
    quest= {'quest':item['quest'],'answers':item['false']}
    quest['answers'].append(item['true'])
    quest = json.dumps(quest)
    id = md5(quest.encode('utf-8')).hexdigest()
    quests.writerow({'ID':id,'QUEST':quest})
    salt = ''.join(random.choices(toSalt,k=10))
    toHash = salt + item['true'] + shadow
    Hash = md5(toHash.encode('utf-8')).hexdigest()
    answers.writerow({'QUEST':id,'SALT':salt,'HASH':Hash})


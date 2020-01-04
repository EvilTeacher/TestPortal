#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import random
import psycopg2 as db
import datetime
import hashlib
import fontforge

from flask import *

db_config = {'dbname':'OStest', 'user':'lector', 'password':'123','host':'localhost'}
app = Flask(__name__)

@app.route('/answer/<int:qid>',methods=['post','get'])
def answer(qid):
    StudId = request.cookies.get('StudId')
    if not StudId: return redirect('/login')

    answ = 'NOTSET'
    if request.method == 'POST' :        
        form = dict(request.form)
        for key in form:
            if type(form[key]) == list:
                form[key] = form[key][0]
        if 'answer' in form : answ = form['answer']
    with db.connect(**db_config) as conn:
        sql = conn.cursor()
        sql.execute("UPDATE results SET stop=%(now)s, answer=%(ans)s " +
                    "WHERE (student=%(sid)s) AND (quest=%(qid)s)",
                    {'now':datetime.datetime.now(),'ans':answ,
                     'sid':StudId,'qid':qid})
        conn.commit()
    return redirect('/')

@app.route('/result')
def result():
    StudId = request.cookies.get('StudId')
    if not StudId: return redirect('/login')    
    with db.connect(**db_config) as conn:
        sql = conn.cursor()
        sql.execute("SELECT quest||'_'||answer FROM results WHERE student = %(sid)s",
                    {'sid':StudId})        
        anwer = set([row[0] for row in sql.fetchall()]) 
        if len(anwer) == 0 : return redirect('/login')
        sql.execute("SELECT id,answer1 FROM quests WHERE id in " +
                    "(SELECT quest FROM results WHERE student = %(sid)s)",
                    {'sid':StudId})        
        true = set(["%d_%s" % (row[0],hashlib.sha1(row[1].encode('utf-8')).hexdigest())
                     for row in sql.fetchall()])
        result = float(float(len(set(anwer & true))) / float(len(true)))
        res = make_response('%.1f %%' % (100*result))
        res.set_cookie('StudId', StudId, max_age=0)
        return res
    
@app.route('/')
def index():
    StudId = request.cookies.get('StudId')
    if not StudId: return redirect('/login')
    data = dict()
    with db.connect(**db_config) as conn:
        sql = conn.cursor()
        
        sql.execute("SELECT count(*) FROM results WHERE student = %(sid)s",{'sid':StudId})
        row = sql.fetchone()
        if int(row[0]) == 0 : return redirect('/login')
        
        sql.execute("SELECT quest FROM results WHERE student = %(sid)s AND (answer = '')",
                    {'sid':StudId})
        q_list = sql.fetchall()
        if not q_list : return redirect('/result')
        qid = str(random.choice([q[0] for q in q_list]))
        sql.execute("SELECT * FROM quests WHERE id=" + qid)
        row = sql.fetchone()
        data['quest'] = {'id':qid, 'text':"[%s/100] %s" % (len(q_list),row[1])}
        data['answers'] = []
        answers = [{'text':row[idx],
                    'code':str(hashlib.sha1(
                        row[idx].encode('utf-8')).hexdigest())}
                   for idx in range(2,len(row))]
        while len(answers) > 0:
            ans = random.choice(answers)
            answers.remove(ans)
            data['answers'].append(ans)
        sql.execute("UPDATE results SET start=%(now)s WHERE "+
                    "(student=%(sid)s) AND (quest=%(qid)s) "+
                    "AND start = '2000-01-01'",
                    {'now':datetime.datetime.now(),
                     'sid':StudId,'qid':qid})
        
    return render_template('index.html',**data)

def create_user(student):
    with db.connect(**db_config) as conn:
        sql = conn.cursor()
        sql.execute("INSERT INTO student VALUES(%(name)s,%(grp)s,%(time)s) "+
                    "ON CONFLICT DO NOTHING RETURNING name||grp ", student)
        sid = sql.fetchone()
        conn.commit()
        if not sid: return None
        sid = hashlib.sha1(sid[0].encode('utf-8')).hexdigest()        
        sql.execute("SELECT id FROM quests")
        all_id = [row[0] for row in sql.fetchall()]     
        count = 0
        while count < (10 if __debug__ else 100):
            count += 1
            quest = random.choice(all_id)
            all_id.remove(quest)
            sql.execute("INSERT INTO results(student,quest) VALUES(%(sid)s, %(quest)s)",
                        {'sid':sid,'quest':quest})
            
        conn.commit()
        return sid        
    return None

@app.route('/login',methods=['post','get'])
def login():
    data = dict()
    if request.method == 'POST':
        form = dict(request.form)
        for key in ['first_name',
                    'second_name',
                    'year',
                    'group']:
            if key not in form: return redirect('/login')            
        for key in form:
            if type(form[key]) == list: form[key] = form[key][0] 
        if (not form['year'].isdigit()) or (len(form['year']) != 4) :
            return redirect('/login')
                
        student = {'name':form ['first_name'] + " " + form['second_name'],
                   'grp':'KKSO-'+form['year'][2:4]+'-'+('%02d' % int(form['group'])),
                   'time': datetime.datetime.now()}
        id = create_user(student)
        
        res = redirect('/')
        if id is not None:
            res.set_cookie('StudId', id, max_age=60*60)
            return res
        data['error'] = "Похоже пользователь уже пытался!"
    
    now = datetime.datetime.now()
    data['years'] = [now.year - idx for idx in range(1,4)]
    return render_template('login.html', **data)
    

if __debug__:
    app.run(host='localhost', debug=True)
else:
    app.run(host='0.0.0.0', port = 80)

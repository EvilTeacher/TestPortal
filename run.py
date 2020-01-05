#!/usr/bin/python3
# -*- coding: utf-8 -*-
from sys import argv
import random
import fontforge
import psycopg2 as db
from hashlib import md5
from getpass import getpass
from flask import *
import datetime
import json

db_config = {'dbname':'OStest', 'user':'lector' ,
             'host':'localhost', 'password':''}
shadow=""
    
app = Flask(__name__)

def build_secret():
    source = []
    for first, last in [(' ','~'), ('А','Я'), ('а','я')]:
        for idx in range(0, ord(last) - ord(first)+1):
            source.append('%c' %(ord(first) + idx))
    for ch in ['Ё','ё']:
        source.append('%c' %(ord(ch)))
    temp = list(set(source))
    dest = []
    while len(temp) > 0 :
        sym = random.choice(temp)
        temp.remove(sym)
        dest.append(sym)
    return dict(zip(source,dest))

def build_font(src_font, secret):
    src = fontforge.open(src_font)
    dst = fontforge.font()
    dst.encoding = 'unicode'
    
    for key in sorted(secret,reverse=True):
        src.selection.select(ord(key))
        src.copy()
        dst.selection.select(ord(secret[key])) 
        dst.paste()

    src.fontname = "EvilTitcher"
    src.familyname = src.fullname = "Evil-Titcher"
    dst.selection.all()
    dst.copy()
    src.selection.all()
    src.paste()
    font_name = ''.join(secret.values()).encode('utf-8')
    font_name = md5(font_name).hexdigest()
    src.generate('./static/'+font_name + '.ttf')
    dst.close()
    src.close()
    return font_name

def encrypt(text, secret):
    words =[]
    for word in text.split():
        words.append(''.join([secret[ch] for ch in word]))
    return secret[' '].join(words)

@app.route('/')
def index():
    StudId = request.cookies.get('StudId')
    if not StudId: return redirect('/login')
    
    data = dict()
    secret = build_secret()
    fname = build_font('font.ttf', secret)
    data['font'] = fname

    with db.connect(**db_config) as conn:
        sql = conn.cursor()
        
        sql.execute("SELECT count(*) FROM results WHERE "+
                    "student = %(sid)s",{'sid':StudId})
        row = sql.fetchone()
        if int(row[0]) == 0 : return redirect('/login')
        
        sql.execute("SELECT quest FROM results WHERE student"+
                    " = %(sid)s AND (answer = '')",
                    {'sid':StudId})
        q_list = sql.fetchall()
        if not q_list : return redirect('/result')
        qid = str(random.choice([q[0] for q in q_list]))
        sql.execute("UPDATE results SET start=%(now)s WHERE "+
                    "(student=%(sid)s) AND (quest=%(qid)s) "+
                    "RETURNING start::text",
                    {'sid':StudId,'qid':qid,
                     'now':datetime.datetime.now()})
        conn.commit()
        time = sql.fetchone()[0]
        
        sql.execute("SELECT quests.quest, truth.salt FROM "+
                    "quests, truth WHERE quests.id=%(q)s "+
                    "and truth.quest=quests.id", {'q':qid})
        quest, salt = sql.fetchone()
        
        data['quest'] = {'id':qid}
        data['quest']['text'] = encrypt(quest['quest'],secret)
        data['answers'] = []
        data['count'] = len(q_list)
        for item in quest['answers']:
            answer = {'text': encrypt(item,secret)}
            toHash = salt + item + shadow
            hKey = md5(toHash.encode('utf-8')).hexdigest()
            toHash = hKey + time + shadow
            Code = md5(toHash.encode('utf-8')).hexdigest()
            answer['code'] = Code
            data['answers'].append(answer)
    return render_template('index.html', **data)


def create_user(student):
    with db.connect(**db_config) as conn:
        sql = conn.cursor()
        sql.execute("INSERT INTO student VALUES(%(name)s, "+
                    "%(grp)s, %(year)s, %(time)s) "+
                    "ON CONFLICT DO NOTHING RETURNING "+
                    "name||grp::text||year::text", student)
        sid = sql.fetchone()
        conn.commit()
        if not sid: return None
        sid = md5(sid[0].encode('utf-8')).hexdigest()        
        sql.execute("SELECT id FROM quests")
        all_id = [row[0] for row in sql.fetchall()]     
        count = 10 if __debug__ else 100
        while (count > 0) and (len(all_id) > 0):
            count -= 1
            quest = random.choice(all_id)
            all_id.remove(quest)
            sql.execute("INSERT INTO results(student, quest)"+
                        " VALUES(%(sid)s, %(quest)s)",
                        {'sid':sid,'quest':quest})
        conn.commit()
        return sid
    return None
@app.route('/login',methods=['post','get'])
def login():
    data = dict()
    if request.method != 'POST':
        now = datetime.datetime.now()
        data['years'] = [now.year - idx for idx in range(1,6)]
        return render_template('login.html', **data)

    form = dict(request.form)
    tmp = len(set(form.keys()) & set(('first_name',
                                     'second_name',
                                      'year', 'group')))
    if tmp != 4: return redirect('/login')
    for key in form:
        if type(form[key]) != list: continue
        form[key] = form[key][0] 

    if not form['year'].isdigit(): return redirect('/login')
    if not form['group'].isdigit(): return redirect('/login')

    name = form ['first_name'] + " " + form['second_name']
    student = {'name':name,
               'grp': int(form['group']),
               'year':int(form['year']),
               'time': datetime.datetime.now()}
    StudId = create_user(student)
    if StudId is None: return redirect('/login')
    
    res = redirect('/')
    res.set_cookie('StudId', StudId, max_age=60*60)
    return res


@app.route('/answer/<string:qid>',methods=['post','get'])
def answer(qid):
    StudId = request.cookies.get('StudId')
    if not StudId: return redirect('/login')
    answer = "TIME_OUT!!!"
    if request.method == 'POST' :
        form = dict(request.form)
        if 'answer' not in form : return redirect('/')
        answer = form['answer']
    val = answer[0] if type(answer) == list else answer

    with db.connect(**db_config) as conn:
        sql = conn.cursor()
        sql.execute("UPDATE results SET stop=%(n)s, "+
                    "answer=%(a)s WHERE (student=%(s)s) "+
                    " AND (quest=%(q)s)",
                    {'n':datetime.datetime.now(),
                     'a':val, 's':StudId, 'q':qid})
        conn.commit()
    return redirect('/')


@app.route('/result')
def result():
    StudId = request.cookies.get('StudId')
    if not StudId: return redirect('/login')    
    full_count, true_count = 0,0
    with db.connect(**db_config) as conn:
        sql = conn.cursor()
        sql.execute("SELECT truth.salt, truth.hash, "+
                    "results.answer, (results.start)::text "+
                    "FROM truth, results WHERE "+
                    "(truth.quest = results.quest) AND "+
                    "results.student = %(id)s", {'id':StudId})
        for salt, truth, answer, time in sql.fetchall():
            toHash = truth + time + shadow
            Hash = md5(toHash.encode('utf-8')).hexdigest()
            true_count += 0 if Hash != answer else 1
            full_count += 1
    result = float(true_count) / float(full_count)
    res = make_response('%.1f %%' % (100*result))
    res.set_cookie('StudId', StudId, max_age=0)
    return res

if __debug__:
    """
    Это адский костыль!!!!
    Запуске в отладочном режиме модуль перезапускется и 
    происходит сброс всего, чего только можно.
    
    Однако, параметры argv остаются теми же, что и перед 
    перезапуском. 
    
    По этой причине, при первом запуске, туда кладем 
    оба пароля!!!!
    
    ps:
    В данном случае, пароль храняться не безопасно, 
    если предположить, что в системе есть внутренний 
    нарушитель! ))))
    """
    if len(argv) == 1:
        argv.append(getpass('Data base password: '))
        argv.append(getpass('Answer password: '))
    db_config['password'] = argv[1]
    shadow = md5(argv[2].encode('utf-8')).hexdigest()
    app.run(host='localhost', debug=True)
else:
    db_config['password'] = getpass('Data base password: ')
    shadow = getpass('Answer password: ')
    shadow = md5(shadow.encode('utf-8')).hexdigest()
    app.run(host='0.0.0.0') #, port = 80)

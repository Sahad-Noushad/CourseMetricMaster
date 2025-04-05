from flask import Flask,request,render_template,redirect,url_for,session,jsonify
import pandas as  pd
from connection import cursor,conn
import math
import re
from matplotlib import pyplot as plt

app=Flask(__name__)
app.secret_key='a34c39e43fb4c9c60a75457b499b4be33a36a713b2052ce621bcba89119b2f2d'

@app.route('/')
def index():
    session['stype']=''
    session['fname']=''
    session['mobile_no']=''
    session['subject']=''
    session['data']=''
    session['rows']=''
    session['threshold']=''
    session['pg_stud_det']=''
    session['co_col_name']=0
    
    return render_template('stafflogin.html')


@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=="POST":
        session['stype']=request.form['cls']
        session['fname']=request.form.get('name')
        session['subject']=request.form.get('sub') #session['subject'] = subject
        password=request.form['pass']
        session['mobile_no']=request.form['mobile_no'] #session['mobile_no'] = mobile no
        cursor.execute("SELECT password,passchange FROM staff WHERE name=? AND type=? AND mobile_number=?",(session['fname'],session['stype'],session['mobile_no'],))
        dbpass=cursor.fetchone() #dbpass = [password,passchange flag]
        if password == dbpass[0]:
            if dbpass[1]==0:
                return redirect(url_for('passchange'))
            else:
                return redirect(url_for('logged'))
        else:
            return render_template('wrongpass.html')
    return render_template('stafflogin.html')

@app.route('/updatedrop')
def updatedrop():
    search=request.args.get('search',type=str)
    val=request.args.get('val',type=str)
    if search == 'name':
        html_string='<option value=" " selected disabled hidden>Name</option>'
        cursor.execute(f"SELECT name FROM staff WHERE type=? ORDER BY name ASC",(val,))
        staff=cursor.fetchall()
        for name in staff:
            html_string+=f"<option value={name[0]}>{name[0]}</option>"
        return jsonify(html_string=html_string)
    if search == 'sub':
        name=request.args.get('name',type=str)
        html_string='<option value=" " selected disabled hidden>Subject</option>'
        cursor.execute("SELECT subject1,subject2,subject3,subject4,subject5 FROM staff WHERE type=? AND name=?",(val,name,))
        subject=cursor.fetchall()
        for subject in subject:
            for subject in subject:
                if subject != None:
                    html_string+=f"<option value={subject}>{subject}</option>"
        return jsonify(html_string=html_string)

@app.route('/passchange',methods=['POST','GET'])
def passchange():
    if request.method=="POST":
        new_pass=request.form['npass']
        confirm_pass=request.form['cpass']
        if new_pass == confirm_pass:
            cursor.execute("UPDATE staff SET passchange=1 , password=? WHERE name=? AND type=? AND mobile_number=?",(new_pass,session['fname'],session['stype'],session['mobile_no'],))
            conn.commit()
            return redirect(url_for('index'))
        else:
            return render_template('staffpasschange.html')
    return render_template('staffpasschange.html')

@app.route('/logged')
def logged():
    cursor.execute("SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type=\"table\" AND name=?)",(session['stype']+'_'+session['subject']+'_co_po',))
    if cursor.fetchone()[0] :
        return redirect(url_for('test'))
    else :
        return render_template('staff.html')   

def copodb(table_name):
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name}(COs VARCHAR(5) PRIMARY KEY,PO1 INT,PO2 INT,PO3 INT,PO4 INT,PO5 INT,PO6 INT,PO7 INT,PO8 INT,PSO1 INT,PSO2 INT,PSO3 INT,PSO4 INT,PSO5 INT,PSO6 INT)")
    conn.commit()

def studb(table_name):
    cursor.execute(f"CREATE TABLE {table_name}(regno INTEGER PRIMARY KEY,name VARCHAR(20),class VARCHAR(10))")
    conn.commit()

@app.route('/copoupload',methods=['POST','GET'])
def copoupload():
    dir='uploads/subject/'+session['stype']+'/'
    if request.method=='POST':
        copo=request.files['co_po']
        std_det=request.files['std']
        threshold=request.form['threshold']
        copo.filename=session['stype']+'_'+session['subject']+'_co_po.xlsx'
        std_det.filename=session['stype']+'_'+session['subject']+'_student.xlsx'
        copo.save(dir+copo.filename)
        std_det.save(dir+std_det.filename)
        tablename=session['stype']+'_'+session['subject']+'_co_po'
        copodb(tablename)
        col_names=['COs','PO1','PO2','PO3','PO4','PO5','PO6','PO7','PO8','PSO1','PSO2','PSO3','PSO4','PSO5','PSO6']
        excel_data=pd.read_excel(copo,header=None,names=col_names,skiprows=[0,1])
        excel_data.to_sql(tablename,conn,if_exists='append',index=False)
        tablename=session['stype']+'_'+session['subject']+'_student'
        studb(tablename)
        col_names=['regno','name','class']
        excel_data=pd.read_excel(std_det,header=None,names=col_names,skiprows=[0])
        excel_data.to_sql(tablename,conn,if_exists='append',index=False)
        cursor.execute("CREATE TABLE IF NOT EXISTS threshold(name VARHCAR(30) PRIMARY KEY,value INT)")
        conn.commit()
        cursor.execute("INSERT INTO threshold (name,value) VALUES (?,?)",(session['stype']+'_'+session['subject'],threshold))
        conn.commit()
    return render_template('test.html',number=['0','0','0','0','0','0'])

@app.route('/test',methods=['POST','GET'])
def test():
    session['picname']=session['stype']+'_'+session['subject']+'_co_attainment.png'
    cursor.execute("SELECT value FROM threshold WHERE name=?",(session['stype']+'_'+session['subject'],))
    threshold=cursor.fetchone()
    session['threshold']=threshold[0]
    print(session['threshold'])
    cursor.execute(f"SELECT COs FROM {session['stype']+'_'+session['subject']+'_co_po'} ORDER BY COs ASC")
    pg_co_no=cursor.fetchall()
    session['pgco']=[]
    for pg_co in pg_co_no:
        for pg in pg_co:
            session['pgco'].append(pg)
    session['co_col_name']=', '.join(session['pgco'])
    cursor.execute(f"SELECT regno,name FROM {session['stype']+'_'+session['subject']+'_student'} ORDER BY regno ASC")
    session['pg_stud_det']=cursor.fetchall()
    cursor.execute("SELECT test,assignment,seminar,model,university,co FROM subtests WHERE subject=?",(session['stype']+'_'+session['subject'],))
    number=cursor.fetchone()
    if number == None:
        cursor.execute("INSERT INTO subtests(subject,test,assignment,seminar,model,university,co) VALUES (?,0,0,0,0,0,0)",(session['stype']+'_'+session['subject'],))
        conn.commit()
        number=["0","0","0","0","0","0"]
    if request.method=='POST':
        session['data']=request.form.get('button') # session['data'] current test name

        if session['stype']=="ug":
            print("ug")
        else:
            print(session['data'])
            if re.match('Test',session['data']) or re.match('Model',session['data']):
                return redirect(url_for('pg_test'))
            if re.match('Assignment',session['data']) or re.match('Seminar',session['data']):
                session['parta']=1
                session['partb']=0
                return render_template('pg_assign_table.html',cono=session['pgco'],student=session['pg_stud_det'])
            if re.match('university',session['data']):
                return render_template('pg_uni_table.html',cono=session['pgco'],student=session['pg_stud_det'])
    return render_template('test.html',number=number)


@app.route('/pg_test',methods=['POST','GET'])
def pg_test():
    char=''
    if request.method=='POST':
        session['date']=request.form['date'] 
        session['starttime']=request.form['starttime']
        session['endtime']=request.form['endtime']
        session['maxmark']=int(request.form['maxmark'])
        session['passmark']=int(request.form['passmark'])
        session['part']=int(request.form['partnumber'])
        print(session['part'])
        for ch in range(97,97+session['part']):
            char=chr(ch)
            print(char)
            session['part'+char]=int(request.form['qn'+char]) #parta qn no
            session['part'+char+'man']=int(request.form['check1'+char]) #parta qn all are mandatory or not

            if session['part'+char+'man']==0:
            
                if int(session['part'+char])%2==0:
            
                    session['part'+char+'spec']=int(request.form['check2'+char]) #parta qn no specify
                    # print(session['part'+char+'spec'])

                    if session['part'+char+'spec']==0:
                        session['part'+char+'noor']=int(request.form['check3'+char]) #part no of or qn
                        # print(session['part'+char+'noor'])

                    else :
                        session['part'+char+'qnno']=int(request.form['qnno'+char]) #part no of or qn spec
                        for i in range(1,session['part'+char+'qnno']+1):
                            session['part'+char+'or'+str(i)+'q1']=int(request.form['part'+char+'or'+str(i)+'qn1'])
                            session['part'+char+'or'+str(i)+'q2']=int(request.form['part'+char+'or'+str(i)+'qn2'])
                    

                else:
                    session['part'+char+'noor']=int(request.form['check3'+char])
        return render_template('pg_test_table.html',cono=session['pgco'],student=session['pg_stud_det'])
    return render_template('pg_data.html')

@app.route('/pg_test_value',methods=['POST','GET'])
def pg_table_value():
    if request.method=='POST':
        session['tablename']=session['data'].lower()+'_'+session['stype']+'_'+session['subject']
        #tablename = test1_pg_eng
        cursor.execute(f"CREATE TABLE {session['tablename']}(regno VARCHAR(15) PRIMARY KEY,name VARCHAR(20),Attendence INT,total_mark INT)")
        conn.commit()

            
        for ch in range(97,97+session['part']):
            char=chr(ch)
            session['part'+char+'_col_name']=[]
            for i in range(1,int(session['part'+char])+1):
                name=char+'q'+str(i)
                #tablename = test1_pg_eng
                cursor.execute(f"ALTER TABLE {session['tablename']} ADD {name} VARCHAR(30)")
                conn.commit()
                session['part'+char+'_col_name'].append(name)

            session['part'+char+'_col']=', '.join(session['part'+char+'_col_name'])
        table_data=request.get_json()
        table_data=table_data['data']
        #tablename = test1_pg_eng
        cursor.execute(f"PRAGMA table_info({session['tablename']})")
        schema=cursor.fetchall()
        col_name=[]
        for info in schema:
            col_name.append(info[1])
        col_names=', '.join(col_name)
        for col_value in table_data:
            col=', '.join(['?' for _ in col_value])
            #tablename = test1_pg_eng
            cursor.execute(f"INSERT INTO {session['tablename']}({col_names}) VALUES ({col})",col_value)
            conn.commit()
        #tablename = test1_pg_eng
        cursor.execute(f"SELECT * FROM {session['tablename']}")
        table_data=cursor.fetchall()
        #tablename = test1_pg_eng_co
        cursor.execute(f"CREATE TABLE {session['tablename']+'_co'}(regno INTEGER PRIMARY KEY,name VARCHAR(20))")
        conn.commit()
        for i in session['pgco']:
            #tablename = test1_pg_eng_co
            cursor.execute(f"ALTER TABLE {session['tablename']+'_co'} ADD {i} INT")
            conn.commit()
        #tablename = test1_pg_eng
            
        for ch in range(97,97+session['part']):
            char=chr(ch)
            cursor.execute(f"SELECT {session['part'+char+'_col']} FROM {session['tablename']} WHERE regno=1")
            session['part'+char+'_cos']=cursor.fetchall()
            cursor.execute(f"SELECT {session['part'+char+'_col']} FROM {session['tablename']} WHERE regno=2")
            session['part'+char+'_maxmark']=cursor.fetchall()

        co_max_marks={}
        for co_col in session['pgco']:
            co_max_marks[co_col]=0
        
        for ch in range(97,97+session['part']):
            char=chr(ch)
            if session['part'+char+'man'] == 1 :
                session['part'+char+'_mark']=man(char,session['pgco'],session['part'+char+'_cos'][0],session['part'+char+'_maxmark'][0])
            else:
                if int(session['part'+char])%2 == 1:
                    session['part'+char+'_mark']=odd(char,session['pgco'],session['part'+char+'_cos'][0],session['part'+char+'_maxmark'][0],session['part'+char+'noor'])
                else :
                    if session['part'+char+'spec']==0:
                        session['part'+char+'_mark']=odd(char,session['pgco'],session['part'+char+'_cos'][0],session['part'+char+'_maxmark'][0],session['part'+char+'noor'])
                    else : 
                        session['part'+char+'_mark']=spec(char,session['pgco'],session['part'+char+'_cos'][0],session['part'+char+'_maxmark'][0],session['part'+char+'qnno'])
            for i in co_max_marks:
                co_max_marks[i]+=session['part'+char+'_mark'][i]

        session['co_col_value']=', '.join('?' for _ in co_max_marks.values())
        #tablename = test1_pg_eng_co
        cursor.execute(f"INSERT INTO {session['tablename']+'_co'}(regno,name,{session['co_col_name']}) VALUES ('1','max mark',{session['co_col_value']})",tuple(co_max_marks.values()))
        conn.commit()

        #tablename = test1_pg_eng
        cursor.execute(f"SELECT regno,name FROM {session['tablename']} WHERE regno NOT IN(1,2) AND Attendence=1 ORDER BY regno ASC")
        session['pg_stud_det']=cursor.fetchall()
        for details in session['pg_stud_det']:
            for ch in range(97,97+session['part']):
                char=chr(ch)
                cursor.execute(f"SELECT {session['part'+char+'_col']} FROM {session['tablename']} WHERE regno={details[0]}")
                session['part'+char+'_maxmark']=cursor.fetchall()
            co_max_marks={}
            for co_col in session['pgco']:
                co_max_marks[co_col]=0

            for ch in range(97,97+session['part']):
                char=chr(ch)
                if session['part'+char+'man'] == 1 :
                    session['part'+char+'_mark']=man(char,session['pgco'],session['part'+char+'_cos'][0],session['part'+char+'_maxmark'][0])
                else:
                    if int(session['part'+char])%2 == 1:
                        session['part'+char+'_mark']=odd(char,session['pgco'],session['part'+char+'_cos'][0],session['part'+char+'_maxmark'][0],session['part'+char+'noor'])
                    else :
                        if session['part'+char+'spec']==0:
                            session['part'+char+'_mark']=odd(char,session['pgco'],session['part'+char+'_cos'][0],session['part'+char+'_maxmark'][0],session['part'+char+'noor'])
                        else : 
                            session['part'+char+'_mark']=spec(char,session['pgco'],session['part'+char+'_cos'][0],session['part'+char+'_maxmark'][0],session['part'+char+'qnno'])
                for i in co_max_marks:
                    co_max_marks[i]+=session['part'+char+'_mark'][i]

            print(co_max_marks)
            cursor.execute(f"INSERT INTO {session['tablename']+'_co'}(regno,name,{session['co_col_name']}) VALUES (?,?,{session['co_col_value']})",(details[0],details[1])+tuple(co_max_marks.values()))
            conn.commit()
        #tablename = test1_pg_eng_co_perc
        cursor.execute(f"CREATE TABLE {session['tablename']+'_co_perc'}(regno INTEGER PRIMARY KEY,name VARCHAR(20))")
        cursor.execute(f"CREATE TABLE {session['tablename']+'_co_threshold'}(regno INTEGER PRIMARY KEY,name VARCHAR(20))")
        conn.commit()
        for i in session['pgco']:
            cursor.execute(f"ALTER TABLE {session['tablename']+'_co_perc'} ADD {i} REAL")
            cursor.execute(f"ALTER TABLE {session['tablename']+'_co_threshold'} ADD {i} INT")
            conn.commit()
        
        cursor.execute(f"SELECT {session['co_col_name']} FROM {session['tablename']+'_co'} WHERE regno=1")
        pg_co_max_value=cursor.fetchone()
        for details in session['pg_stud_det']:
            cursor.execute(f"SELECT {session['co_col_name']} FROM {session['tablename']+'_co'} WHERE regno={details[0]}")
            pg_co_stud_max=cursor.fetchone()
            pg_co_stud_perc=[]
            pervalue=[]
            for i in range(0,int(len(pg_co_max_value))):
                perc=(pg_co_stud_max[i]/pg_co_max_value[i])*100
                per=round(perc,1)
                if per >= int(session['threshold']):
                    pervalue.append("Y")
                else:
                    pervalue.append("N")
                pg_co_stud_perc.append(per)
            cursor.execute(f"INSERT INTO {session['tablename']+'_co_perc'}(regno,name,{session['co_col_name']}) VALUES (?,?,{session['co_col_value']})",(details[0],details[1])+tuple(pg_co_stud_perc))
            cursor.execute(f"INSERT INTO {session['tablename']+'_co_threshold'}(regno,name,{session['co_col_name']}) VALUES (?,?,{session['co_col_value']})",(details[0],details[1])+tuple(pervalue))
            conn.commit()

        cursor.execute(f"SELECT {session['co_col_name']} FROM {session['tablename']+'_co_threshold'} WHERE regno NOT IN(0)")
        threshold=cursor.fetchall()
        co_count={}
        for i in range(0,len(session['pgco'])):
            co_count[i]=0
        for i in range(0,len(session['pgco'])):
            for val in threshold:
                if val[i] == "Y":
                    co_count[i]+=1
        cursor.execute(f"INSERT INTO {session['tablename']+'_co_threshold'}(regno,name,{session['co_col_name']}) VALUES ('0','total number',{session['co_col_value']})",(tuple(co_count.values())))
        conn.commit()
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {session['data']}(id INTEGER PRIMARY KEY AUTOINCREMENT,type CHAR(5),subject VARCHAR(15),date VARCHAR(15),start_time VARCHAR(15),end_time VARCHAR(15),max_mark INT,pass_mark INT,part_a INT,part_b INT,part_c INT,part_d INT,threshold REAL)")
        conn.commit()
        cursor.execute(f"INSERT INTO {session['data']}(type,subject,date,start_time,end_time,max_mark,pass_mark,part_a,part_b,part_c,part_d,threshold) VALUES (?,?,?,?,?,?,?,?,?,0,0,?)",(session['stype'],session['subject'],session['date'],session['starttime'],session['endtime'],session['maxmark'],session['passmark'],session['parta'],session['partb'],session['threshold']))
        conn.commit()
        list=['test','assignment','seminar','model']
        for nlist in list:
            if nlist in session['data'].lower():
                table=nlist
        cursor.execute(f"UPDATE subtests SET {table}={table}+1 WHERE subject=?",(session['stype']+'_'+session['subject'],))
        conn.commit()
    return redirect(url_for('test'))

#mandatory mark
def man(char,cos,part_cos,part_maxmark):
    session['part'+char+'_mark']={}
    for i in cos:
        session['part'+char+'_mark'][i]=0
    for i in range(0,len(part_maxmark)):
        value=part_maxmark[i]
        if value != None :
            for j in session['part'+char+'_mark']:
                if part_cos[i]==j:
                    session['part'+char+'_mark'][j]+=int(value)
    return session['part'+char+'_mark']

def odd(char,cos,part_cos,part_maxmark,noor):
    session['part'+char+'_mark']={}
    part_maxmark=list(part_maxmark)
    part_maxmark=[str(i or '0') for i in part_maxmark]
    part_cos=list(part_cos)
    print(part_maxmark)
    print(part_cos)
    for i in cos:
        session['part'+char+'_mark'][i]=0
    for i in range(0,noor):
        max_mark=max(part_maxmark)
        ind=part_maxmark.index(max_mark)
        for i in session['part'+char+'_mark']:
            if part_cos[ind]==i:
                session['part'+char+'_mark'][i]+=int(max_mark)
                part_maxmark.pop(ind)
                part_cos.pop(ind)
    return session['part'+char+'_mark']

def spec(char,cos,part_cos,part_maxmark,qnno):
    session['part'+char+'_mark']={}
    for i in cos:
        session['part'+char+'_mark'][i]=0
    for i in range(1,qnno+1):
        a=int(session['part'+char+'or'+str(i)+'q1'])-1
        b=int(session['part'+char+'or'+str(i)+'q2'])-1
        if part_maxmark[a] != None and part_maxmark[b] != None:
            if part_maxmark[a] >= part_maxmark[b]:
                max_mark=part_maxmark[a]
                ind=a
            else:
                max_mark=part_maxmark[b]
                ind=b
        else:
            if part_maxmark[a] == None:
                max_mark=part_maxmark[b]
                ind=b
            else:
                max_mark=part_maxmark[a]
                ind=a
        for i in session['part'+char+'_mark']:
            if part_cos[ind]==i:
                session['part'+char+'_mark'][i]+=int(max_mark)
    return session['part'+char+'_mark']


@app.route('/pg_assign_value',methods=['POST','GET'])
def pg_assign_value():
    if request.method=='POST':
        session['tablename']=session['data'].lower()+'_'+session['stype']+'_'+session['subject']
        cursor.execute(f"CREATE TABLE {session['tablename']}(regno VARCHAR(15) PRIMARY KEY,name VARCHAR(20),Attendence INT)")
        conn.commit()
        session['parta_col_name']=[]
        for i in range(1,int(session['parta'])+1):
            name='aq'+str(i)
            cursor.execute(f"ALTER TABLE {session['tablename']} ADD {name} VARCHAR(30)")
            conn.commit()
            session['parta_col_name'].append(name)
        session['parta_col']=', '.join(session['parta_col_name'])
        table_data=request.get_json()
        table_data=table_data['data']
        cursor.execute(f"PRAGMA table_info({session['tablename']})")
        schema=cursor.fetchall()
        col_name=[]
        for info in schema:
            col_name.append(info[1])
        col_names=', '.join(col_name)
        for col_value in table_data:
            col=', '.join(['?' for _ in col_value])
            cursor.execute(f"INSERT INTO {session['tablename']}({col_names}) VALUES ({col})",col_value)
            conn.commit()
        cursor.execute(f"SELECT * FROM {session['tablename']}")
        table_data=cursor.fetchall()
        cursor.execute(f"CREATE TABLE {session['tablename']+'_co'}(regno INTEGER PRIMARY KEY,name VARCHAR(20))")
        conn.commit()
        for i in session['pgco']:
            cursor.execute(f"ALTER TABLE {session['tablename']+'_co'} ADD {i} INT")
            conn.commit()
        cursor.execute(f"SELECT {session['parta_col']} FROM {session['tablename']} WHERE regno=1")
        session['parta_cos']=cursor.fetchall()
        cursor.execute(f"SELECT {session['parta_col']} FROM {session['tablename']} WHERE regno=2")
        parta_maxmark=cursor.fetchall()
        co_max_marks={}
        for co_col in session['pgco']:
            co_max_marks[co_col]=0
        session['co_col_value'],co_max_mark=co_mark_cal_parta(session['parta_cos'],parta_maxmark,co_max_marks)
        cursor.execute(f"INSERT INTO {session['tablename']+'_co'}(regno,name,{session['co_col_name']}) VALUES ('1','max mark',{session['co_col_value']})",tuple(co_max_mark.values()))
        conn.commit()

        cursor.execute(f"SELECT regno,name FROM {session['tablename']} WHERE regno NOT IN(1,2) AND Attendence=1 ORDER BY regno ASC")
        session['pg_stud_det']=cursor.fetchall()
        for details in session['pg_stud_det']:
            cursor.execute(f"SELECT {session['parta_col']} FROM {session['tablename']} WHERE regno={details[0]}")
            parta_maxmark=cursor.fetchall()
            co_max_marks={}
            for co_col in session['pgco']:
                co_max_marks[co_col]=0
            session['co_col_value'],co_max_mark=co_mark_cal_parta(session['parta_cos'],parta_maxmark,co_max_marks)
            cursor.execute(f"INSERT INTO {session['tablename']+'_co'}(regno,name,{session['co_col_name']}) VALUES (?,?,{session['co_col_value']})",(details[0],details[1])+tuple(co_max_mark.values()))
            conn.commit()
        cursor.execute(f"CREATE TABLE {session['tablename']+'_co_perc'}(regno INTEGER PRIMARY KEY,name VARCHAR(20))")
        cursor.execute(f"CREATE TABLE {session['tablename']+'_co_threshold'}(regno INTEGER PRIMARY KEY,name VARCHAR(20))")
        conn.commit()
        for i in session['pgco']:
            cursor.execute(f"ALTER TABLE {session['tablename']+'_co_perc'} ADD {i} REAL")
            cursor.execute(f"ALTER TABLE {session['tablename']+'_co_threshold'} ADD {i} INT")
            conn.commit()

        cursor.execute(f"SELECT {session['co_col_name']} FROM {session['tablename']+'_co'} WHERE regno=1")
        pg_co_max_value=cursor.fetchone()
        for details in session['pg_stud_det']:
            cursor.execute(f"SELECT {session['co_col_name']} FROM {session['tablename']+'_co'} WHERE regno={details[0]}")
            pg_co_stud_max=cursor.fetchone()
            pg_co_stud_perc=[]
            pervalue=[]
            for i in range(0,int(len(pg_co_max_value))):
                if pg_co_max_value[i] != 0:
                    perc=(pg_co_stud_max[i]/pg_co_max_value[i])*100
                    per=round(perc,1)
                else:
                    per=0
                if per >= int(session['threshold']):
                    pervalue.append("Y")
                else:
                    pervalue.append("N")
                pg_co_stud_perc.append(per)
                    
            print(session['co_col_name'],session['co_col_value'],pg_co_stud_perc)
            cursor.execute(f"INSERT INTO {session['tablename']+'_co_perc'}(regno,name,{session['co_col_name']}) VALUES (?,?,{session['co_col_value']})",(details[0],details[1])+tuple(pg_co_stud_perc))
            cursor.execute(f"INSERT INTO {session['tablename']+'_co_threshold'}(regno,name,{session['co_col_name']}) VALUES (?,?,{session['co_col_value']})",(details[0],details[1])+tuple(pervalue))
            conn.commit()

        cursor.execute(f"SELECT {session['co_col_name']} FROM {session['tablename']+'_co_threshold'} WHERE regno NOT IN(0)")
        threshold=cursor.fetchall()
        co_count={}
        for i in range(0,len(session['pgco'])):
            co_count[i]=0
        for i in range(0,len(session['pgco'])):
            for val in threshold:
                if val[i] == "Y":
                    co_count[i]+=1
        cursor.execute(f"INSERT INTO {session['tablename']+'_co_threshold'}(regno,name,{session['co_col_name']}) VALUES ('0','total number',{session['co_col_value']})",(tuple(co_count.values())))
        conn.commit()
        list=['test','assignment','seminar','model']
        for nlist in list:
            if nlist in session['data'].lower():
                table=nlist
        cursor.execute(f"UPDATE subtests SET {table}={table}+1 WHERE subject=?",(session['stype']+'_'+session['subject'],))
        conn.commit()
    return redirect(url_for('test'))

@app.route('/pg_uni_value',methods=['POST','GET'])
def pg_uni_value():
    if request.method=='POST':
        session['tablename']=session['data'].lower()+'_'+session['stype']+'_'+session['subject']
        cursor.execute(f"CREATE TABLE {session['tablename']}(regno VARCHAR(15) PRIMARY KEY,name VARCHAR(20),Attendence INT)")
        conn.commit()
        for i in session['pgco']:
            cursor.execute(f"ALTER TABLE {session['tablename']} ADD {i} INT")
            conn.commit()
        table_data=request.get_json()
        table_data=table_data['data']
        print(table_data)
        cursor.execute(f"PRAGMA table_info({session['tablename']})")
        schema=cursor.fetchall()
        col_name=[]
        for info in schema:
            col_name.append(info[1])
        col_names=', '.join(col_name)
        for col_value in table_data:
            col=', '.join(['?' for _ in col_value])
            print(col_names,col,col_value)
            cursor.execute(f"INSERT INTO {session['tablename']}({col_names}) VALUES ({col})",col_value)
            conn.commit()
        cursor.execute(f"SELECT * FROM {session['tablename']}")
        table_data=cursor.fetchall()
        cursor.execute(f"CREATE TABLE {session['tablename']+'_co_perc'}(regno INTEGER PRIMARY KEY,name VARCHAR(20))")
        cursor.execute(f"CREATE TABLE {session['tablename']+'_co_threshold'}(regno INTEGER PRIMARY KEY,name VARCHAR(20))")
        conn.commit()
        for i in session['pgco']:
            cursor.execute(f"ALTER TABLE {session['tablename']+'_co_perc'} ADD {i} REAL")
            cursor.execute(f"ALTER TABLE {session['tablename']+'_co_threshold'} ADD {i} INT")
            conn.commit()
        session['co_col_value']=', '.join('?' for _ in session['pgco'])
        cursor.execute(f"SELECT regno,name FROM {session['tablename']} WHERE regno NOT IN(1) AND Attendence=1 ORDER BY regno ASC")
        session['pg_stud_det']=cursor.fetchall()
        cursor.execute(f"SELECT {session['co_col_name']} FROM {session['tablename']} WHERE regno=1")
        pg_co_max_value=cursor.fetchone()
        for details in session['pg_stud_det']:
            cursor.execute(f"SELECT {session['co_col_name']} FROM {session['tablename']} WHERE regno={details[0]}")
            pg_co_stud_max=cursor.fetchone()
            pg_co_stud_perc=[]
            pervalue=[]
            for i in range(0,int(len(pg_co_max_value))):
                if pg_co_max_value[i] != 0:
                    perc=(pg_co_stud_max[i]/pg_co_max_value[i])*100
                    per=round(perc,1)
                else:
                    per=0
                if per >= int(session['threshold']):
                    pervalue.append("Y")
                else:
                    pervalue.append("N")
                pg_co_stud_perc.append(per)
            
            cursor.execute(f"INSERT INTO {session['tablename']+'_co_perc'}(regno,name,{session['co_col_name']}) VALUES (?,?,{session['co_col_value']})",(details[0],details[1])+tuple(pg_co_stud_perc))
            cursor.execute(f"INSERT INTO {session['tablename']+'_co_threshold'}(regno,name,{session['co_col_name']}) VALUES (?,?,{session['co_col_value']})",(details[0],details[1])+tuple(pervalue))
            conn.commit()

        cursor.execute(f"SELECT {session['co_col_name']} FROM {session['tablename']+'_co_threshold'} WHERE regno NOT IN(0)")
        threshold=cursor.fetchall()
        co_count={}
        for i in range(0,len(session['pgco'])):
            co_count[i]=0
        for i in range(0,len(session['pgco'])):
            for val in threshold:
                if val[i] == "Y":
                    co_count[i]+=1
        cursor.execute(f"INSERT INTO {session['tablename']+'_co_threshold'}(regno,name,{session['co_col_name']}) VALUES ('0','total number',{session['co_col_value']})",(tuple(co_count.values())))
        conn.commit()
        list=['test','assignment','seminar','model','university']
        for nlist in list:
            if nlist in session['data'].lower():
                table=nlist
        cursor.execute(f"UPDATE subtests SET {table}={table}+1 WHERE subject=?",(session['stype']+'_'+session['subject'],))
        conn.commit()
    return redirect(url_for('test'))

def co_mark_cal_parta(parta_cos,parta_maxmark,co_max_mark):
    for i in range(0,int(session['parta'])):
        for co_col in session['pgco']:
            if parta_cos[0][i]==co_col:
                if parta_maxmark[0][i] != None:
                    co_max_mark[co_col]+=int(parta_maxmark[0][i])
    co_max_mark=dict(sorted(co_max_mark.items()))
    session['co_col_value']=', '.join('?' for _ in co_max_mark.values())
    return(session['co_col_name'],session['co_col_value'],co_max_mark)

@app.route('/co_attain',methods=['GET','POST'])
def co_attain():
    cursor.execute("SELECT test,model,assignment,seminar FROM subtests WHERE subject=?",(session['stype']+'_'+session['subject'],))
    result=cursor.fetchone()
    session['co_col_value']=', '.join(['?' for _ in session['pgco']])
    co_value_list={}
    co_avg_list={}
    list=['test','model','assignment','seminar']
    for item in list:
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {session['stype']+'_'+session['subject']+'_'+item}(regno INTEGER PRIMARY KEY,name VARCHAR(20))")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {session['stype']+'_'+session['subject']+'_'+item+'_threshold'}(regno INTEGER PRIMARY KEY,name VARCHAR(20))")
        conn.commit()
        for i in session['pgco']:
            cursor.execute(f"ALTER TABLE {session['stype']+'_'+session['subject']+'_'+item} ADD {i} REAL")
            cursor.execute(f"ALTER TABLE {session['stype']+'_'+session['subject']+'_'+item+'_threshold'} ADD {i} VARCHAR(1)")
            conn.commit()
        for co_col in session['pgco']:
            co_value_list[co_col]=[]
        for details in session['pg_stud_det']:
            for i in range(1,int(result[list.index(item)])+1):
                tablename=item+str(i)+'_'+session['stype']+'_'+session['subject']+'_co_perc'
                cursor.execute(f"SELECT {session['co_col_name']} FROM {tablename} WHERE regno={details[0]}")
                co_value=cursor.fetchone()
                if co_value is not None:
                    for co_col in session['pgco']:
                        co=co_value[session['pgco'].index(co_col)]
                        if co != 0:
                            co_value_list[co_col].append(co)
            for co_col in session['pgco']:
                if len(co_value_list[co_col]) != 0:
                    co_avg_list[co_col]=round(math.fsum(co_value_list[co_col])/len(co_value_list[co_col]),1)
            if math.fsum(co_avg_list.values()) != 0:
                cursor.execute(f"INSERT INTO {session['stype']+'_'+session['subject']+'_'+item}(regno,name,{session['co_col_name']}) VALUES (?,?,{session['co_col_value']})",(details[0],details[1])+tuple(co_avg_list.values()))
                conn.commit()
            for co_col in session['pgco']:
                co_value_list[co_col]=[]
                co_avg_list[co_col]=0
            cursor.execute(f"SELECT {session['co_col_name']} FROM {session['stype']+'_'+session['subject']+'_'+item} WHERE regno={details[0]}")
            co_val=cursor.fetchone()
            co_val_threshold=[]
            if co_val is not None:
                for co in co_val:
                    if co >= int(session['threshold']):
                        co_val_threshold.append("Y")
                    else:
                        co_val_threshold.append("N")
                cursor.execute(f"INSERT INTO {session['stype']+'_'+session['subject']+'_'+item+'_threshold'}(regno,name,{session['co_col_name']}) VALUES (?,?,{session['co_col_value']})",(details[0],details[1])+tuple(co_val_threshold))
                conn.commit()
                    
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {session['stype']+'_'+session['subject']+'_internal'}(regno INTEGER PRIMARY KEY,name VARCHAR(20))")
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {session['stype']+'_'+session['subject']+'_assign'}(regno INTEGER PRIMARY KEY,name VARCHAR(20))")
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {session['stype']+'_'+session['subject']+'_internal_threshold'}(regno INTEGER PRIMARY KEY,name VARCHAR(20))")
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {session['stype']+'_'+session['subject']+'_assign_threshold'}(regno INTEGER PRIMARY KEY,name VARCHAR(20))")
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {session['stype']+'_'+session['subject']+'_co_attainment'}(sino INT PRIMARY KEY,name VARCHAR(30))")
    conn.commit()
    for i in session['pgco']:
        cursor.execute(f"ALTER TABLE {session['stype']+'_'+session['subject']+'_internal'} ADD {i} REAL")
        cursor.execute(f"ALTER TABLE {session['stype']+'_'+session['subject']+'_assign'} ADD {i} REAL")
        cursor.execute(f"ALTER TABLE {session['stype']+'_'+session['subject']+'_internal_threshold'} ADD {i} INT")
        cursor.execute(f"ALTER TABLE {session['stype']+'_'+session['subject']+'_assign_threshold'} ADD {i} INT")
        cursor.execute(f"ALTER TABLE {session['stype']+'_'+session['subject']+'_co_attainment'} ADD {i} REAL")
    conn.commit()
    list=['test','model']
    for details in session['pg_stud_det']:
        for item in list:
            tablename=session['stype']+'_'+session['subject']+'_'+item
            cursor.execute(f"SELECT {session['co_col_name']} FROM {tablename} WHERE regno={details[0]}")
            co_value=cursor.fetchone()
            if co_value is not None:
                for co_col in session['pgco']:
                    co=co_value[session['pgco'].index(co_col)]
                    if co != 0:
                        co_value_list[co_col].append(co)
        pg_internal_threshold=[]
        for co_col in session['pgco']:
            if len(co_value_list[co_col]) != 0:
                co_avg_list[co_col]=round(math.fsum(co_value_list[co_col])/len(co_value_list[co_col]),1)
        if math.fsum(co_avg_list.values()) != 0:
            cursor.execute(f"INSERT INTO {session['stype']+'_'+session['subject']+'_internal'}(regno,name,{session['co_col_name']}) VALUES (?,?,{session['co_col_value']})",(details[0],details[1])+tuple(co_avg_list.values()))
            conn.commit()
        for co_col in session['pgco']:
            co_value_list[co_col]=[]
            co_avg_list[co_col]=0
    for details in session['pg_stud_det']:
        cursor.execute(f"SELECT {session['co_col_name']} FROM {session['stype']+'_'+session['subject']+'_internal'} WHERE regno={details[0]}")
        pg_internal=cursor.fetchone()
        pg_internal_threshold=[]
        for internal in pg_internal:
            if internal >= int(session['threshold']):
                pg_internal_threshold.append("Y")
            else:
                pg_internal_threshold.append("N")
        cursor.execute(f"INSERT INTO {session['stype']+'_'+session['subject']+'_internal_threshold'}(regno,name,{session['co_col_name']}) VALUES (?,?,{session['co_col_value']})",(details[0],details[1])+tuple(pg_internal_threshold))
        conn.commit()
    cursor.execute(f"SELECT {session['co_col_name']} FROM {session['stype']+'_'+session['subject']+'_internal_threshold'}")
    threshold=cursor.fetchall()
    co_count={}
    for i in range(0,len(session['pgco'])):
        co_count[i]=0
    for i in range(0,len(session['pgco'])):
        for val in threshold:
            if val[i] == "Y":
                co_count[i]+=1
    cursor.execute(f"INSERT INTO {session['stype']+'_'+session['subject']+'_internal_threshold'}(regno,name,{session['co_col_name']}) VALUES ('0','total number',{session['co_col_value']})",(tuple(co_count.values())))
    conn.commit()
    cursor.execute(f"SELECT COUNT(*) FROM {session['stype']+'_'+session['subject']+'_internal_threshold'} WHERE regno NOT IN(0)")
    no_of_stud=cursor.fetchone()
    cursor.execute(f"SELECT {session['co_col_name']} FROM {session['stype']+'_'+session['subject']+'_internal_threshold'} WHERE regno=0")
    no_of_co=cursor.fetchone()
    co_perc=[]
    for val in no_of_co:
        perc=(val/no_of_stud[0])*100
        co_perc.append(round(perc,1))
    cursor.execute(f"INSERT INTO {session['stype']+'_'+session['subject']+'_co_attainment'}(sino,name,{session['co_col_name']}) VALUES (1,'Internal(test+model)',{session['co_col_value']})",(tuple(co_perc)))
    conn.commit()

    list=['assignment','seminar']
    for details in session['pg_stud_det']:
        for item in list:
            tablename=session['stype']+'_'+session['subject']+'_'+item
            cursor.execute(f"SELECT {session['co_col_name']} FROM {tablename} WHERE regno={details[0]}")
            co_value=cursor.fetchone()
            if co_value is not None:
                for co_col in session['pgco']:
                    co=co_value[session['pgco'].index(co_col)]
                    if co != 0:
                        co_value_list[co_col].append(co)
        pg_internal_threshold=[]
        for co_col in session['pgco']:
            if len(co_value_list[co_col]) != 0:
                co_avg_list[co_col]=round(math.fsum(co_value_list[co_col])/len(co_value_list[co_col]),1)
        if math.fsum(co_avg_list.values()) != 0:
            cursor.execute(f"INSERT INTO {session['stype']+'_'+session['subject']+'_assign'}(regno,name,{session['co_col_name']}) VALUES (?,?,{session['co_col_value']})",(details[0],details[1])+tuple(co_avg_list.values()))
            conn.commit()
        for co_col in session['pgco']:
            co_value_list[co_col]=[]
            co_avg_list[co_col]=0
    for details in session['pg_stud_det']:
        cursor.execute(f"SELECT {session['co_col_name']} FROM {session['stype']+'_'+session['subject']+'_assign'} WHERE regno={details[0]}")
        pg_internal=cursor.fetchone()
        pg_internal_threshold=[]
        for internal in pg_internal:
            if internal >= int(session['threshold']):
                pg_internal_threshold.append("Y")
            else:
                pg_internal_threshold.append("N")
        cursor.execute(f"INSERT INTO {session['stype']+'_'+session['subject']+'_assign_threshold'}(regno,name,{session['co_col_name']}) VALUES (?,?,{session['co_col_value']})",(details[0],details[1])+tuple(pg_internal_threshold))
        conn.commit()
    cursor.execute(f"SELECT {session['co_col_name']} FROM {session['stype']+'_'+session['subject']+'_assign_threshold'}")
    threshold=cursor.fetchall()
    co_count={}
    for i in range(0,len(session['pgco'])):
        co_count[i]=0
    for i in range(0,len(session['pgco'])):
        for val in threshold:
            if val[i] == "Y":
                co_count[i]+=1
    cursor.execute(f"INSERT INTO {session['stype']+'_'+session['subject']+'_assign_threshold'}(regno,name,{session['co_col_name']}) VALUES ('0','total number',{session['co_col_value']})",(tuple(co_count.values())))
    conn.commit()
    cursor.execute(f"SELECT COUNT(*) FROM {session['stype']+'_'+session['subject']+'_assign_threshold'} WHERE regno NOT IN(0)")
    no_of_stud=cursor.fetchone()
    cursor.execute(f"SELECT {session['co_col_name']} FROM {session['stype']+'_'+session['subject']+'_assign_threshold'} WHERE regno=0")
    no_of_co=cursor.fetchone()
    co_perc=[]
    for val in no_of_co:
        perc=(val/no_of_stud[0])*100
        co_perc.append(round(perc,1))
    cursor.execute(f"INSERT INTO {session['stype']+'_'+session['subject']+'_co_attainment'}(sino,name,{session['co_col_name']}) VALUES (2,'Assignment + Seminar',{session['co_col_value']})",(tuple(co_perc)))
    conn.commit()

    cursor.execute(f"SELECT COUNT(*) FROM {'university_'+session['stype']+'_'+session['subject']+'_co_threshold'} WHERE regno NOT IN(0)")
    no_of_stud=cursor.fetchone()
    cursor.execute(f"SELECT {session['co_col_name']} FROM {'university_'+session['stype']+'_'+session['subject']+'_co_threshold'} WHERE regno=0")
    no_of_co=cursor.fetchone()
    co_perc=[]
    for val in no_of_co:
        perc=(val/no_of_stud[0])*100
        co_perc.append(round(perc,1))
    cursor.execute(f"INSERT INTO {session['stype']+'_'+session['subject']+'_co_attainment'}(sino,name,{session['co_col_name']}) VALUES (3,'University Mark',{session['co_col_value']})",(tuple(co_perc)))
    conn.commit()

    cursor.execute(f"SELECT {session['co_col_name']} FROM {session['stype']+'_'+session['subject']+'_co_attainment'} WHERE sino NOT IN(0) ORDER BY sino ASC")
    values=cursor.fetchall()
    for i in values:
        for j in session['pgco']:
            if i[session['pgco'].index(j)] != 0:
                co_value_list[j].append(i[session['pgco'].index(j)])
    for i in session['pgco']:
        co_value_list[i]=round(math.fsum(co_value_list[i])/len(co_value_list[i]),1)
    
    cursor.execute(f"INSERT INTO {session['stype']+'_'+session['subject']+'_co_attainment'}(sino,name,{session['co_col_name']}) VALUES (0,'Total avg',{session['co_col_value']})",(tuple(co_value_list.values())))
    conn.commit()
    filepath='static/images/'+session['picname']
    cursor.execute(f"SELECT {session['co_col_name']} FROM {session['stype']+'_'+session['subject']+'_co_attainment'} WHERE sino=0")
    result=cursor.fetchall()
    y=[]
    for i in result:
        for j in range(0,len(i)):
            y.append(i[j])
    plt.bar(session['pgco'],y)
    plt.title(f"CO ATTAINMENT {session['subject']+','+session['stype']}")
    plt.axhline(y=40,color='k',linestyle='dashed')
    plt.savefig(filepath)

    cursor.execute(f"CREATE TABLE IF NOT EXISTS {session['stype']+'_'+session['subject']+'_po_attainment'} AS SELECT * FROM {session['stype']+'_'+session['subject']+'_co_po'}")
    conn.commit()
    cursor.execute(f"SELECT {session['co_col_name']} FROM {session['stype']+'_'+session['subject']+'_co_attainment'} WHERE sino=0")
    data=list(cursor.fetchone())
    for i in range(0,len(data)):
        if data[i] >= 40:
            data[i]='Y'
        else:
            data[i]='N'
    cursor.execute(f"ALTER TABLE {session['stype']+'_'+session['subject']+'_po_attainment'} ADD COT VARCHAR(1)")
    conn.commit()
    for i in range(0,len(session['pgco'])):
        print(data[i])
        print(session['pgco'][i])
        cursor.execute(f"UPDATE {session['stype']+'_'+session['subject']+'_po_attainment'} SET COT='{data[i]}' WHERE COs='{session['pgco'][i]}'")
    conn.commit()
    po_total={}
    po_mark={}
    po={}
    po_perc=['PO_Attainment']
    po_threshold=['PO_Attained']
    po_col=['COs','PO1','PO2','PO3','PO4','PO5','PO6','PO7','PO8','PSO1','PSO2','PSO3','PSO4','PSO5','PSO6']
    po_name='PO1,PO2,PO3,PO4,PO5,PO6,PO7,PO8,PSO1,PSO2,PSO3,PSO4,PSO5,PSO6'
    for co in session['pgco']:
        cursor.execute(f"SELECT {po_name} FROM {session['stype']+'_'+session['subject']+'_po_attainment'} WHERE COs='{co}'")
        po_total[co]=list(cursor.fetchone())
        po_total[co]=[x or 0 for x in po_total[co]]
        cursor.execute(f"SELECT {po_name} FROM {session['stype']+'_'+session['subject']+'_po_attainment'} WHERE COs='{co}' AND COT='Y'")
        data=cursor.fetchone()
        if data != None:
            po_mark[co]=list(data)
            po_mark[co]=[x or 0 for x in po_mark[co]]
    po_mark = list(map(sum,zip(*po_mark.values())))
    po_total = list(map(sum,zip(*po_total.values())))
    for i in range(0,len(po_total)):
        perc=round((po_mark[i]/po_total[i])*100,1)
        po_perc.append(perc)
        if perc >= 40:
            po_threshold.append('Y')
        else:
            po_threshold.append('N')
    tablename=session['stype']+'_'+session['subject']+'_po_attainment'
    cursor.execute("INSERT INTO {}({}) VALUES ({})".format(tablename,', '.join(po_col),', '.join(['?'] * len(po_col))),po_perc)
    cursor.execute("INSERT INTO {}({}) VALUES ({})".format(tablename,', '.join(po_col),', '.join(['?'] * len(po_col))),po_threshold)
    conn.commit()

    cursor.execute("UPDATE subtests SET co=co+1 WHERE subject=?",(session['stype']+'_'+session['subject'],))
    conn.commit()
    return redirect(url_for('codata'))

@app.route('/codata',methods=['GET','POST'])
def codata():
    cursor.execute(f"SELECT name,{session['co_col_name']} FROM {session['stype']+'_'+session['subject']+'_co_attainment'}")
    table1=cursor.fetchall()
    cursor.execute(f"SELECT * FROM {session['stype']+'_'+session['subject']+'_po_attainment'}")
    table3=cursor.fetchall()
    print(table3)
    item=['test','model','assignment','seminar']
    co_full={}
    for i in item:
        co_full[i]={}
        for data in session['pg_stud_det']:
            co_full[i][data[0]]=[]
            co_full[i][data[0]].append(data[0])
            co_full[i][data[0]].append(data[1])
    for data in session['pg_stud_det']:
        for i in item:
            cursor.execute(f"SELECT {session['co_col_name']} FROM {session['stype']+'_'+session['subject']+'_'+i} WHERE regno={data[0]}")
            result=cursor.fetchone()
            cursor.execute(f"SELECT {session['co_col_name']} FROM {session['stype']+'_'+session['subject']+'_'+i+'_threshold'} WHERE regno={data[0]}")
            result_thre=cursor.fetchone()
            for j in range(0,len(session['pgco'])):
                if result is not None:
                    co_full[i][data[0]].append(result[j])
                else:
                    co_full[i][data[0]].append("-")
                if result_thre is not None:
                    co_full[i][data[0]].append(result_thre[j])
                else:
                    co_full[i][data[0]].append("-")
    return render_template('codata.html',table1=table1,table3=table3,table2=co_full,pic=session['picname'],co=session['pgco'],stud=session['pg_stud_det'],item=item)
    

@app.route('/testdata',methods=['GET','POST'])
def testdata():
    passdata=request.get_json()
    value=passdata['data']
    cursor.execute(f"SELECT * FROM {value} WHERE type=? AND subject=?",(session['stype'],session['subject'],))
    session['rows']=cursor.fetchall()
    return ("success")

@app.route('/testdbshow')
def testdbshow():
    return render_template('testdbshow.html',rows=session['rows'],type=session['stype'])

if __name__=="__main__":
    app.run(debug=True)
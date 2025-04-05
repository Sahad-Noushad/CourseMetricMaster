from flask import Flask, render_template, redirect, url_for, request
import os
import pandas as pd
from connection import cursor,conn

app = Flask(__name__)

UPLOAD_PATH='uploads/'
app.config['UPLOAD_PATH'] = UPLOAD_PATH

def parse(filepath,type):
    col_names=['name','mobile_number','subject1','subject2','subject3','subject4','subject5']
    exceldata=pd.read_excel(filepath,names=col_names,header=None,skiprows=[0])
    exceldata['passchange']=0
    exceldata['password']=exceldata['mobile_number'].apply(lambda x: str(x)) 
    if type == "ug":
        exceldata['type']="ug"
    else:
        exceldata['type']="pg"
    exceldata.to_sql('staff',conn,if_exists="append",index=False)

@app.route('/')
def home():
    return render_template('admin.html')

@app.route('/datadb')
def datadb():
    tablenames={}
    cursor.execute("SELECT subject FROM subtests")
    tables=cursor.fetchall()
    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%{table[0]}%'")
        tablenames[table[0]]=cursor.fetchall()
    return render_template("datadb.html",tablenames=tablenames)

@app.route('/db',methods=['GET','POST'])
def db():
    db_name=request.form['dbname']
    print(db_name)
    cursor.execute(f"SELECT * FROM {db_name}")
    table=cursor.fetchall()
    cursor.execute(f"PRAGMA table_info({db_name})")
    schema=cursor.fetchall()
    return render_template("db.html",name=db_name,table=table,schema=schema)

@app.route('/dbdrop',methods=['GET','POST'])
def dbdrop():
    dbname=request.form['db_name']
    print(dbname)
    cursor.execute(f"DROP TABLE {dbname}")
    conn.commit()
    return redirect(url_for('datadb'))

@app.route('/excel')
def excel():
    cursor.execute("SELECT * FROM staff")
    details=cursor.fetchall()
    return render_template("data.html",details=details)

@app.route('/upload', methods=['POST'])
def upload():
    if request.method=="POST":
        ug=request.files['ug']
        pg=request.files['pg']
        ugfile=(os.path.join(app.config['UPLOAD_PATH'],ug.filename))
        pgfile=(os.path.join(app.config['UPLOAD_PATH'],pg.filename))
        ug.save(ugfile)
        pg.save(pgfile)
        parse(ugfile,'ug')
        parse(pgfile,'pg')
        return redirect(url_for('excel'))
    return render_template('admin.html')

if __name__ == '__main__':
    cursor.execute("CREATE TABLE IF NOT EXISTS staff(mobile_number INT PRIMARY KEY,name VARCHAR(50) NOT NULL,type CHAR(2) NOT NULL,subject1 VARCHAR(15),subject2 VARCHAR(15),subject3 VARCHAR(15),subject4 VARCHAR(15),subject5 VARCHAR(15),passchange INT NOT NULL,password VARCHAR(20) NOT NULL)")
    sql=("CREATE TABLE IF NOT EXISTS subtests(subject VARCHAR(20) PRIMARY KEY,test INT,assignment INT,seminar INT,model INT,university INT,co INT)")
    cursor.execute(sql)
    conn.commit()
    app.run(debug=True)
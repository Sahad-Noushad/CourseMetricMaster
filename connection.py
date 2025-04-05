import sqlite3 as sql

conn=sql.connect('staff.db',check_same_thread=False)
cursor=conn.cursor()
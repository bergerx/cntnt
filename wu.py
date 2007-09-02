#!/usr/bin/python
# TODO: implement getopt.
import sqlite
import sys

conn = sqlite.connect('/home/bekir/test/python/hede.db')
c = conn.cursor()

# Create table
#c.execute('''CREATE TABLE "contents" (id INTEGER NOT NULL PRIMARY KEY UNIQUE, contentid INTEGER NOT NULL, content VARCHAR, label VARCHAR, type VARCHAR, parent INTEGER NOT NULL, startver INTEGER NOT NULL, endver INTEGER, createdate VARCHAR NOT NULL, deletedate VARCHAR);''')

# Insert a row of data
# c.execute('''INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, endver, createdate, deletedate) VALUES ( , , , , , , , , , )''')

# Insert root record
# c.execute('''INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, createdate) VALUES (0 ,0 ,"root" ,"root" ,"content" ,0 , 0, "20070818100000" )''')


def tree(c, id=0, level=0):
	c.execute("select * from contents where parent=%d"% (id))
	a=c.fetchall()
	#print a
	for i in a:
		print "%4d %s%s(%s)"%(i.id, " "*level*4, i.content, i.type)
		tree(c, i.id, level+1)

if len(sys.argv)==5 and sys.argv[1]=="add":
	c.execute('select max(id) as ver from contents')
	nextid = int(1 + c.fetchone().ver)
	# sys.argv = add content, type, parent
	text= 'INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, createdate) VALUES (%s ,%s , "%s" ,"" ,"%s" ,%s , %s, "20070818100000" )'%(nextid, nextid, sys.argv[2], sys.argv[3], sys.argv[4], nextid)
	print text
	c.execute(text)
elif len(sys.argv)==2 and sys.argv[1]=="tree":
	tree(c)
elif len(sys.argv)==2 and sys.argv[1]=="all":
	c.execute('select * from contents')
	for row in c:
		print row#.content
else:
	print "possible parameters: add, tree, all"
# c.execute('''INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, createdate) VALUES (1 ,1 ,"types" ,"types" ,"content" ,0 , 0, "20070818100000" )''')
# c.execute('''INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, createdate) VALUES (2 ,2 ,"views" ,"views" ,"content" ,0 , 0, "20070818100000" )''')
# c.execute('''INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, createdate) VALUES (3 ,3 ,"roles" ,"roles" ,"content" ,0 , 0, "20070818100000" )''')
# c.execute('''INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, createdate) VALUES (4 ,4 ,"ops" ,"ops" ,"content" ,0 , 0, "20070818100000" )''')
# c.execute('''INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, createdate) VALUES (5 ,5 ,"users" ,"users" ,"content" ,0 , 0, "20070818100000" )''')
# c.execute('''INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, createdate) VALUES (6 ,6 ,"contents" ,"contents" ,"content" ,0 , 0, "20070818100000" )''')

conn.commit()


#!/usr/bin/python
import sqlite
import sys, getopt


def usage():
	print """Usage:
"""

def connect():
	conn = sqlite.connect('/home/bekir/test/python/hede.db')
	c = conn.cursor()
	return conn, c
# Create table
#c.execute('''CREATE TABLE "contents" (id INTEGER NOT NULL PRIMARY KEY UNIQUE, contentid INTEGER NOT NULL, content VARCHAR, label VARCHAR, type VARCHAR, parent INTEGER NOT NULL, startver INTEGER NOT NULL, endver INTEGER, createdate VARCHAR NOT NULL, deletedate VARCHAR);''')
# Insert a row of data
# c.execute('''INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, endver, createdate, deletedate) VALUES ( , , , , , , , , , )''')
# Insert root record
# c.execute('''INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, createdate) VALUES (0 ,0 ,"root" ,"root" ,"content" ,0 , 0, "20070818100000" )''')

def disconnect(conn):
	conn.commit()

def tree(c, id=0, level=0):
	try:
		c.execute("select * from contents where parent=%s"% (id))
	except:
		print "Content has no childs"
	all=c.fetchall()
	for i in all:
		print "%4d %s%s(%s)"%(i.id, " "*level*4, i.content, i.type)
		tree(c, i.id, level+1)

def view(c, id=None):
	if id == None:
		c.execute("select * from contents")
	else:
		c.execute("select * from contents where id=%s"%id)
	all=c.fetchall()
	for i in all:
		print "%4d %4d %s %s(%s)"%(i.id, i.parent, i.label, i.content, i.type)

def read(c, id):
	try:
		c.execute("select * from contents where id=%s"%id)
		return c.fetchone()
	except:
		return False

def create(c, content="", type="", parent=0, label=""):
	# TODO: Add parameter check
	c.execute('select max(id) as ver from contents')
	nextid = int(1 + c.fetchone().ver)
	sql = 'INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, createdate) VALUES (%s ,%s , "%s" ,"%s" ,"%s" ,%s , %s, "20070818100000" )'
	sql = sql % (nextid, nextid, content, label, type, parent, nextid)
	#print sql
	c.execute(sql)
	id = c.lastrowid
	return read(c, id)

def delete(c, id):
	c.execute('select id from contents where parent = %s' % id)
	childs = c.fetchall()
	if len(childs)!=0:
		print "Content has childs. Not deleted. Try -D parameter.%s"%len(childs)
		sys.exit(1)
	sql = 'delete from contents where id = %s' % (id)
	c.execute(sql)

def deepDelete(c, id):
	c.execute('select id from contents where parent = %s' % (id))
	childs = c.fetchall()
	for child in childs:
		deepDelete(c, child.id)
	else:
		delete(c, id)

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "ho:crudDt", ["help", "output=", "id=", "content=", "label=", "type=", "parent="])
	except getopt.GetoptError:
		usage()
		sys.exit(2)

	content = None
	label = None
	type = None
	parent = None
	crud = None
	id = None

	for o, a in opts:
		if o in ("-h", "--help"):
			usage()
			sys.exit(0)
		if o in ("-o", "--output"):
			print a
		if o == "-c":
			crud = "create"
		if o == "-r":
			crud = "read"
		if o == "-u":
			crud = "update"
		if o == "-d":
			crud = "delete"
		if o == "-D":
			crud = "deepdelete"
		if o == "-t":
			crud = "tree"
		if o == "--id":
			id = a
		if o == "--content":
			content = a
		if o == "--label":
			label = a
		if o == "--type":
			type = a
		if o == "--parent":
			parent = a

	print """no error"""

	conn, c = connect()

	if crud == "create":
		if None in (content, type, parent):
			print "You must supply --content, --type and --parent"
			sys.exit(0)
		create(c, content, type, parent, label)
	elif crud == "read":
		view(c, id)
	elif crud == "tree":
		if id == None: id=0
		tree(c, id)
	elif crud == "update":
		pass
	elif crud == "delete":
		delete(c, id)
	elif crud == "deepdelete":
		deepDelete(c, id)
	else:
		usage()

	disconnect(conn)
	sys.exit(0)

if __name__=="__main__":
	main()

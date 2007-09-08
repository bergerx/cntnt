#!/usr/bin/python
import sqlite
import sys, re, datetime

class cntnt:
	# TODO: Add parameter check
	def __init__(self, dbfile):
		self.conn = sqlite.connect(dbfile)
		self.c = self.conn.cursor()

	def commit(self):
		self.conn.commit()

	def revert(self):
		self.conn.revert()

	def read(self, id):
		#TODO: add a flag named "followPointer" for pointer typed contents
		try:
			self.c.execute("select * from contents where id=%s"%id)
			result = self.c.fetchone()
			self.commit()
		except:
			result = False
			self.revert()
		#TODO: read must returns a dict
		return result

	def readChilds(self, id):
		try:
			self.c.execute("select * from contents where parent=%s"% (id))
		except:
			return False
		result = []
		childs = self.c.fetchall()
		for child in childs:
			result.append(self.read(child.id))
		return result or False

# Create table
#c.execute('''CREATE TABLE "contents" (id INTEGER NOT NULL PRIMARY KEY UNIQUE, contentid INTEGER NOT NULL, content VARCHAR, label VARCHAR, type VARCHAR, parent INTEGER NOT NULL, startver INTEGER NOT NULL, endver INTEGER, createdate VARCHAR NOT NULL, deletedate VARCHAR);''')
# Insert a row of data
# c.execute('''INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, endver, createdate, deletedate) VALUES ( , , , , , , , , , )''')
# Insert root record
# c.execute('''INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, createdate) VALUES (0 ,0 ,"root" ,"root" ,"content" ,0 , 0, "20070818100000" )''')
	def create(self, content="", type="", parent=0, label=""):
		#TODO: Check if type is defined
		# Check if label and type names are valid
		def checkName(string):
			return bool(re.match("^[A-Za-z0-9]*$",string))
		if not checkName(label) or not checkName(type):
			return False
		# Check if parent exists
		self.c.execute('select * from contents where id=%s' % parent)
		if not self.c.fetchone():
			return False
		# Check if label is uniq
		self.c.execute('select * from contents where parent=%s and label="%s"' % (parent, label))
		if label != "" and self.c.fetchone():
			return False
		# Get next content id
		self.c.execute('select max(contentid) as ver from contents')
		nextcid = int(1 + self.c.fetchone().ver)
		# Get next version number(id)
		self.c.execute('select max(id) as ver from contents')
		nextid = int(1 + self.c.fetchone().ver)
		# Create record
		createdate = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
		sql = 'INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, createdate) VALUES (%s ,%s , "%s" ,"%s" ,"%s" ,%s , %s, "%s" )'
		sql = sql % (nextid, nextcid, content, label, type, parent, nextid, createdate)
		self.c.execute(sql)
		id = self.c.lastrowid
		return self.read(id)

	def delete(self, id):
		# Check if id exists
		if not self.read(id):
			return None
		# Check if content has childs
		self.c.execute('select id from contents where parent = %s' % id)
		childs = self.c.fetchall()
		if len(childs)!=0:
			return False
		#TODO: delete() must UPDATE records (not DELETE) to be marked as deleted
		# Delete record
		sql = 'delete from contents where id = %s' % (id)
		self.c.execute(sql)
		self.commit()
		return id

	def deepDelete(self, id):
		self.c.execute('select id from contents where parent = %s' % (id))
		childs = self.c.fetchall()
		ids = []
		for child in childs:
			child_ids = self.deepDelete(child.id)
			ids.extend(child_ids)
		else:
			id = self.delete(id)
			if id:
				ids.append(id)
		if not ids:
			result = False
		else:
			result = ids
		# Return a list of deleted ids
		return result

# here after there is only command line functions
def tree(cnt, id=0, level=0):
	childs = cnt.readChilds(id)
	if not childs:
		return False
	for child in childs:
		print "%4d %s%s(%s)"%(child.id, " "*level*4, child.content, child.type)
		tree(cnt, child.id, level+1)

def view(cnt, id=None):
	#TODO: Show all records - MASSIVE FUNCTION
	all=[]
	for i in all:
		print "%4d %4d %s %s(%s)"%(i.id, i.parent, i.label, i.content, i.type)


def usage():
	print """Usage:
"""

def main():
	import getopt
	cnt = cntnt('/home/bekir/test/python/hede.db')
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

	if crud == "create":
		if None in (content, type, parent):
			print "You must supply --content, --type and --parent"
			sys.exit(0)
		return cnt.create(content, type, parent, label)
	elif crud == "read":
		view(cnt, id)
	elif crud == "tree":
		if id == None: id=0
		tree(cnt, id)
	elif crud == "update":
		pass
	elif crud == "delete":
		return cnt.delete(id)
	elif crud == "deepdelete":
		return cnt.deepDelete(id)
	else:
		usage()
	sys.exit(0)

if __name__=="__main__":
	main()

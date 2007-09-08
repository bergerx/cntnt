#!/usr/bin/python
import sqlite
import sys, re, datetime

class cntnt:

	# Exception Definitions
	class LabelNameError(Exception): pass
	class TypeNameError(Exception): pass
	class ContentNotExixtsError(Exception): pass
	class LabelNotUniqError(Exception): pass
	class ContentHasChilds(Exception): pass
	class ContentHasNoChilds(Exception): pass

	# TODO: Add parameter check
	def __init__(self, dbfile):
		self.conn = sqlite.connect(dbfile)
		self.c = self.conn.cursor()

	def commit(self):
		self.conn.commit()

	def revert(self):
		self.conn.revert()

	def read(self, id, followPointer = True, isPointed = False):
		self.c.execute('SELECT * FROM contents WHERE contentid = %s AND deletedate IS NULL'%id)
		row = self.c.fetchone()
		# Check if row exists
		if not row:
			raise self.ContentNotExixtsError
		# If content is a pointer
		if followPointer == True and row.type == 'ptr':
			return self.read(row[content], isPointed = True)
		# Prepare result dict
		result = {}
		for key in row.keys():
			result[key] = row[key]
		# Add extra keys for pointers, etc.
		result['isPointed'] = isPointed
		return result

	def readChilds(self, id):
		self.c.execute('SELECT * FROM contents WHERE parent = %s AND deletedate IS NULL'% (id))
		result = []
		childs = self.c.fetchall()
		for child in childs:
			result.append(self.read(child.id))
		return result

# Create table
#c.execute('''CREATE TABLE "contents" (id INTEGER NOT NULL PRIMARY KEY UNIQUE, contentid INTEGER NOT NULL, content VARCHAR, label VARCHAR, type VARCHAR, parent INTEGER NOT NULL, startver INTEGER NOT NULL, endver INTEGER, createdate VARCHAR NOT NULL, deletedate VARCHAR);''')
# Insert a row of data
# c.execute('''INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, endver, createdate, deletedate) VALUES ( , , , , , , , , , )''')
# Insert root record
# c.execute('''INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, createdate) VALUES (0 ,0 ,"root" ,"root" ,"content" ,0 , 0, "20070818100000" )''')
	def create(self, content="", type="", parent=0, label=""):
		# TODO: Check if type is defined
		# Check if label and type names are valid
		def checkName(string):
			return bool(re.match("^[A-Za-z0-9]*$",string))
		if not checkName(type):
			raise self.TypeNameError, 'Error in type name validation: "%s"' % type
		if not checkName(label):
			raise self.LabelNameError, 'Error in label name validation: "%s"' % label
		# Check if parent exists
		self.read(parent)
		self.c.execute('SELECT * FROM contents WHERE parent=%s AND label="%s" AND deletedate IS NULL' % (parent, label))
		if label != "" and self.c.fetchone():
			raise self.LabelNotUniqError, "Check label:%s" % label
		# Get next content id
		self.c.execute('SELECT MAX(contentid) AS contentid FROM contents')
		nextcid = int(1 + self.c.fetchone().contentid)
		# Get next version number(id)
		self.c.execute('SELECT MAX(id) AS ver FROM contents')
		nextid = int(1 + self.c.fetchone().ver)
		# Create record
		createdate = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
		sql = 'INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, createdate) VALUES (%s ,%s , "%s" ,"%s" ,"%s" ,%s , %s, "%s" )'
		sql = sql % (nextid, nextcid, content, label, type, parent, nextid, createdate)
		self.c.execute(sql)
		self.commit()
		return self.read(nextcid)

	def delete(self, id):
		# Check if content id exists
		self.read(id)
		# Check if content has childs
		childs = self.readChilds(id)
		if len(childs) != 0:
			raise ContentHasChilds, "Content has %s childs" % len(childs)
		# Delete record
		deletedate = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
		sql = 'UPDATE contents SET deletedate = "%s" WHERE contentid = %s AND deletedate IS NULL' % (deletedate, id)
		self.c.execute(sql)
		self.commit()
		return id

	def deepDelete(self, id):
		ids = []
		for child in self.readChilds(id):
			childIds = self.deepDelete(child["contentid"])
			ids.extend(childIds)
		self.delete(id)
		ids.append(int(id))
		# Return a list of deleted ids
		return ids

# here after there is only command line functions
def tree(cnt, id=0, level=0):
	childs = cnt.readChilds(id)
	for child in childs:
		print "%4d %s%s(%s)"%(child["id"], " "*level*4, child["content"], child["type"])
		tree(cnt, child["id"], level+1)

def view(cnt, id=None):
	# TODO: Show all records - MASSIVE FUNCTION
	i=cnt.read(id)
	print "%4d %4d %s %s(%s)"%(i["id"], i["parent"], i["label"], i["content"], i["type"])


def usage():
	print """Usage:
"""

def main():
	import getopt
	cnt = cntnt('hede.db')
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
		print cnt.create(content, type, parent, label)
	elif crud == "read":
		view(cnt, id)
	elif crud == "tree":
		if id == None: id=0
		tree(cnt, id)
	elif crud == "update":
		pass
	elif crud == "delete":
		print cnt.delete(id)
	elif crud == "deepdelete":
		print cnt.deepDelete(id)
	else:
		usage()
	sys.exit(0)

if __name__=="__main__":
	main()

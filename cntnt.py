#!/usr/bin/python
import sqlite
import sys, re, datetime

class cntnt:

	# Exception Definitions
	class LabelNameError(Exception): pass
	class TypeNameError(Exception): pass
	class ContentExistsError(Exception): pass
	class ContentNotExistsError(Exception): pass
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
		self.c.execute('SELECT * FROM contents WHERE contentid = "%s" AND deletedate IS NULL'%id)
		row = self.c.fetchone()
		# Check if row exists
		if not row:
			raise self.ContentNotExistsError, 'ID not exists:"%s"' % id
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

	def readChilds(self, id, label = "", type = ""):
		sqlexpr = ""
		if label != "":
			sqlexpr += 'AND label = "%s"' % label
		if type != "":
			sqlexpr += 'AND type = "%s"' % type
		self.c.execute('SELECT * FROM contents WHERE parent = %s AND deletedate IS NULL %s' % (id, sqlexpr))
		result = []
		childs = self.c.fetchall()
		for child in childs:
			result.append(self.read(child.contentid))
		return result

	def checkForCreate(self, content="", type="", parent=0, label="", id=0):
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
		# Check if content id exists
		try:
			if id and self.read(id):
				raise self.ContentExistsError, "Content already exists which has this id:%s" % id
		except self.ContentNotExistsError:
			pass

# Create table
# c.execute('''CREATE TABLE "contents" (id INTEGER NOT NULL PRIMARY KEY UNIQUE, contentid INTEGER NOT NULL, content VARCHAR, label VARCHAR, type VARCHAR, parent INTEGER NOT NULL, startver INTEGER NOT NULL, endver INTEGER, createdate VARCHAR NOT NULL, deletedate VARCHAR);''')
# Insert a row of data
# c.execute('''INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, endver, createdate, deletedate) VALUES ( , , , , , , , , , )''')
# Insert root record
# c.execute('''INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, createdate) VALUES (0 ,0 ,"root" ,"root" ,"content" ,0 , 0, "20070818100000" )''')
	def create(self, content="", type="", parent=0, label="", id=0):
		# Do creation parameter checks, raises exception on parameter errors
		self.checkForCreate(content=content, type=type, parent=parent, label=label, id=id)
		# Get next version number(id) if its not given
		if not id:
			self.c.execute('SELECT MAX(contentid) AS contentid FROM contents')
			id = int(1 + self.c.fetchone().contentid)
		self.c.execute('SELECT MAX(id) AS ver FROM contents')
		ver = int(1 + self.c.fetchone().ver)
		# Create record
		createdate = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
		sql = 'INSERT INTO "contents" (id, contentid, content, label, type, parent, startver, createdate) VALUES ("%s" ,"%s" , "%s" ,"%s" ,"%s" ,"%s" , "%s", "%s" )'
		sql = sql % (ver, id, content, label, type, parent, ver, createdate)
		self.c.execute(sql)
		self.commit()
		return self.read(id)

	def delete(self, id):
		# Check if content id exists
		self.read(id)
		# Check if content has childs
		childs = self.readChilds(id)
		if len(childs) != 0:
			raise ContentHasChilds, "Content has %s childs" % len(childs)
		# Delete record
		deletedate = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
		sql = 'UPDATE contents SET deletedate = "%s" WHERE contentid = "%s" AND deletedate IS NULL' % (deletedate, id)
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

	def update(self, id, content="", type="", parent=0, label=""):
		# Do creation parameter checks, raises exception on parameter errors
		try:
			self.checkForCreate(content=content, type=type, parent=parent, label=label, id=id)
		except self.ContentExistsError:
			pass
		cnt = self.read(id)
		self.delete(id)
		if content: cnt["content"] = content
		if type: cnt["type"] = type
		if parent: cnt["parent"] = parent
		if label: cnt["label"] = label
		# FIXME: if new label exist or label/type names are not valid content will be deleted only
		return self.create(content=content, type=type, parent=parent, label=label, id=id)

	def getCPath(self, path, parent = 0):
		# FIXME: Not implemented yet
		branchExpr, residual = path.split(".",1)
		arr = []
		for id in self.executeBranchExpr(parent, branchExpr):
			childIds = getCPath(residual, id)
			arr.extend(childIds)
		return arr

	def executeBranchExpr(self, parent, expr):
		# FIXME: Not implemented yet
		# Type expression
#		if expr[0,2] == "__":
			# TODO: Not implenmented type expressions
#			type = expr[2:]
#			return []
		#Label expression
		if expr[0] == "_":
			label = expr[1:]
			return self.readChilds(parent, label = label)
		return []

# here after there is only command line functions
def tree(cnt, id=0, level=0):
	childs = cnt.readChilds(id)
	for child in childs:
		output = "%4d %s" % (child["contentid"], " "*level*4)
		output += child["content"]
		if child["label"]:
			output += "[%s]" % child["label"]
		output += "(%s)" % child["type"]
		print output
		tree(cnt, child["contentid"], level+1)

def usage():
	print """Usage:
"""

def main():
	import getopt
	cnt = cntnt('hede.db')
	try:
		opts, args = getopt.getopt(sys.argv[1:], "ho:crudDt", ["help", "output=", "id=", "content=", "label=", "type=", "parent=", "path="])
	except getopt.GetoptError:
		usage()
		sys.exit(2)

	content = ""
	label = ""
	type = ""
	parent = 0
	crud = None
	id = 0
	path = ""

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
		if o == "--path":
			path = a

	if crud == "create":
		if "" in (content, type, parent):
			print "You must supply --content, --type and --parent"
			sys.exit(0)
		print cnt.create(content=content, type=type, parent=parent, label=label, id=id)
	elif crud == "read":
		if path:
			print cnt.getCPath(path)
		if id:
			print cnt.read(id)
	elif crud == "tree":
		tree(cnt, id)
	elif crud == "update":
		print cnt.update(id=id, content=content, type=type, parent=parent, label=label)
	elif crud == "delete":
		print cnt.delete(id)
	elif crud == "deepdelete":
		print cnt.deepDelete(id)
	else:
		usage()
	sys.exit(0)

if __name__=="__main__":
	main()

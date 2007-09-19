#!/usr/bin/python
import sqlite3
import sys, re, datetime
import logging

logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s %(levelname)-8s %(message)s',
					datefmt='%Y%m%d%H%M%S',
					filename='cntnt.log')

# For debugging (logging) sql queries
class CntntCursor(sqlite3.Cursor):
	def execute(self, *args, **kwargs):
		logging.debug(args)
		sqlite3.Cursor.execute(self, *args, **kwargs)

# Prepare result dict_factory for sqlite3 cursor results
def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d


class cntnt:

	# Constant Definitions
	POINTER_TYPE_NAME = "ptr"
	TYPE_LABEL_REGEX = "^[A-Za-z0-9]*$"

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
		self.conn = sqlite3.connect(dbfile)
		self.conn.row_factory = dict_factory
		self.c = self.conn.cursor(factory=CntntCursor)

	def commit(self):
		self.conn.commit()

	def revert(self):
		self.conn.revert()

	def read(self, id, followPointer = True, isPointed = False,
			 pointedFrom = None):
		self.c.execute('''SELECT * FROM contents
			WHERE contentid = ? AND deletedate IS NULL''', (id,))
		row = self.c.fetchone()
		# Check if row exists
		if not row:
			raise self.ContentNotExistsError, 'ID not exists:"%s"' % id
		# Add extra keys for pointers, etc.
		row['isPointed'] = isPointed
		row['pointedFrom'] = pointedFrom
		# If content is a pointer
		if followPointer == True and row["type"] == self.POINTER_TYPE_NAME:
			return self.read(row["content"], isPointed = True,
							 pointedFrom = id)
		return row

	def readChilds(self, id, label = None, type = None, content = None,
				   followPointer = True, followPointerSelf = True):
		# followPointerSelf will be needed for reading any pointers
		# child contents.
		# followPointer will be needed for deep delete.
		sqlexpr = ""
		# FIXME: sql injection risc for label and type. Using directly
		# substitution for variables in sql query.
		if label:
			sqlexpr += ' AND label = "%s"' % label
		if type:
			sqlexpr += ' AND type = "%s"' % type
		if content:
			sqlexpr += ' AND content = "%s"' % content
		if followPointerSelf:
			myself = self.read(id)
			id = myself["contentid"]
		self.c.execute('''SELECT * FROM contents
			WHERE parent = ? AND deletedate IS NULL %s'''%sqlexpr, (id,))
		result = []
		childs = self.c.fetchall()
		for child in childs:
			result.append(self.read(child["contentid"],
									followPointer=followPointer))
		return result

	def checkForCreate(self, content="", type="", parent=0, label="", id=0):
		# TODO: Check if type is defined
		# Check if label and type names are valid
		def checkName(string):
			return bool(re.match(self.TYPE_LABEL_REGEX, string))
		if not checkName(type):
			raise self.TypeNameError, 'Error in type name validation: "%s"' % type
		if not checkName(label):
			raise self.LabelNameError, 'Error in label name validation: "%s"' % label
		# Check if parent exists (exception for root record)
		not id and self.read(parent)
		self.c.execute('''SELECT * FROM contents
			WHERE label = ? AND parent = ? AND deletedate IS NULL''', (label, parent))
		if label != "" and self.c.fetchone():
			raise self.LabelNotUniqError, "Check label:%s" % label
		# Check if content id exists
		try:
			if id and self.read(id):
				raise self.ContentExistsError, "Content already exists which has this id:%s" % id
		except self.ContentNotExistsError:
			pass

	def create(self, content="", type="", parent=0, label="", id=0):
		# TODO: If declared a "label" for parent's type definition for
		# this type of content use that label as default.

		# Do creation parameter checks, raises exception on parameter
		# errors
		self.checkForCreate(content=content, type=type, parent=parent,
			label=label, id=id)
		# Get next version number(id) if its not given
		if not id:
			self.c.execute('SELECT MAX(contentid) AS contentid FROM contents')
			id = int(1 + self.c.fetchone()["contentid"])
		self.c.execute('SELECT MAX(id) AS ver FROM contents')
		ver = int(1 + self.c.fetchone()["ver"])
		# Create record
		createdate = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
		sql = '''INSERT INTO "contents" (id, contentid, content, label,
			type, parent, startver, createdate) VALUES (? ,? ,
			? ,? ,? ,? , ?, ? )'''
		where = (ver,id,content,label,type,parent,ver,createdate)
		self.c.execute(sql, where)
		self.conn.cursor()
		self.commit()
		return self.read(id)

	def delete(self, id, followPointer = False, force = False):
		# Check if content id exists
		self.read(id, followPointer=followPointer)
		# Check if content has childs
		childs = self.readChilds(id, followPointer=followPointer)
		if not force and len(childs) != 0:
			raise self.ContentHasChilds, "Content(%s) has %s childs" % (id, len(childs))
		# Delete record
		deletedate = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
		c = self.conn.cursor()
		self.c.execute('''UPDATE contents SET deletedate=? WHERE contentid=?
			AND deletedate IS NULL''', ((deletedate,id)))
		self.commit()
		return id

	def deepDelete(self, id):
		# FIXME: This function deletes pointer targets instead of
		# pointer contetnts itself.

		# We must use pointedFrom key from read contents.
		ids = []
		for child in self.readChilds(id):
			notPointedId = child["pointedFrom"] or child["contentid"]
			childIds = self.deepDelete(notPointedId)
			ids.extend(childIds)
		self.delete(id)
		ids.append(int(id))
		# Return a list of deleted ids
		return ids

	def update(self, id, content="", type="", parent=0, label=""):
		# Update not allowed for root
		if not id: return self.read(0)
		# Do creation parameter checks, raises exception on parameter
		# errors
		try:
			self.checkForCreate(content=content, type=type,
				parent=parent, label=label, id=id)
		except self.ContentExistsError:
			pass
		cnt = self.read(id)
		self.delete(id, force = True)
		if content: cnt["content"] = content
		if type: cnt["type"] = str(type)
		if parent: cnt["parent"] = int(parent)
		if label: cnt["label"] = str(label)
		# FIXME: if new label exist or label/type names are not valid
		# content will be deleted only
		return self.create(content=content, type=type, parent=parent,
			label=label, id=id)

	def getCPath(self, path, parent = 0):
		# TODO: Implement pylex lib for this parsing function
		
		# FIXME: Not working for CPaths which includes parenthesis,
		# and code looks like cryptic.
		
		# Some exaple CPaths:
		# _basic._views.__view(_name=view1)
		# _basic._views.__view(__text=view1)
		# _basic._views.__view(@view1)
		# _basic._views.__view(_type._name=type1)
		# _basic._views.__view(_type.@type1)
		# _basic._views.__view.@goruntu1
		# _basic._views.__view._type.@type1
		def intersection(list1, list2):
			return [i for i in list1 if i in list2]
		parsedExprs = self.getBranchExpr(path)
		for i, parsedExpr in enumerate(parsedExprs):
			if i>=1: parsedExpr['parent'] = parsedExprs[i-1]['contentids']
			else: parsedExpr['parent'] = [parent]
			children = self.calculateExprChilds(parsedExpr)
			# Calculate children from exression given in paren
			if parsedExpr['paren']:
				parenChildren = []
				if i>=1:
					parsedExpr['paren'][0]['parent'] = children
				else:
					parsedExpr['paren'][0]['parent'] = [parent]
				for p in parsedExpr['paren']:
					parenChildren.extend(self.calculateExprChilds(p))
				children = intersection(children, parenChildren)
			parsedExpr['contentids']=children
		return parsedExprs[-1]['contentids']

	def calculateExprChilds(self, parsedExpr):
		results = []
		for p in parsedExpr['parent']:
			content=None
			if parsedExpr['type'] and parsedExpr['type'].count('='):
				type, content = parsedExpr['type'].split('=')
			else:
				type = parsedExpr['type']
			if parsedExpr['label'] and parsedExpr['label'].count('='):
				label, content = parsedExpr['label'].split('=')
			else:
				label = parsedExpr['label']
			contents = self.readChilds(
					p, type = type, label = label,
					content = content or parsedExpr['content'])
			results.extend([item['contentid'] for item in contents])
		return results

	def getBranchExpr(self, path):
		contents = []
		if path[0] != '.':
			path = '.' + path
		for all, text, paren in re.findall('\.(([^(.]*)(\([^)]*\))?)', path):
			# Type expression: "__typename[n]" or "__typename"
			result = {'parent':[], 'type':None, 'label':None, 'content':None,
					  'paren':[], 'parenChilds':[], 'contentids':[]}
			if len(text) > 2 and text[0:2] == "__":
				result['type'] = text[2:]
			#Label expression: "_labelname"
			elif len(text) > 1 and text[0] == "_":
				result['label'] = text[1:]
			elif len(text) > 1 and text[0] == "@":
				result['content'] = text[1:]
			if paren:
				result['paren'] = self.getBranchExpr(paren[1:-1])
			contents.append(result)
		return contents

# here after there is only command line functions
def tree(cnt, id=0, level=0):
	childs = cnt.readChilds(id, followPointer = False)
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
	 -[c|r|u|d|D|t] --id= --content= --label= --type= --parent= --path=
"""

def main():
	import getopt
	cnt = cntnt('cntnt.db3')
	try:
		opts, args = getopt.getopt(sys.argv[1:], "ho:crudDt", ["help",
			"output=", "id=", "content=", "label=", "type=", "parent=",
			"path="])
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
		if o in ("-o", "--output"): print a
		if o == "-c": crud = "create"
		if o == "-r": crud = "read"
		if o == "-u": crud = "update"
		if o == "-d": crud = "delete"
		if o == "-D": crud = "deepdelete"
		if o == "-t": crud = "tree"
		if o == "--id": id = int(a)
		if o == "--content": content = str(a)
		if o == "--label": label = str(a)
		if o == "--type": type = str(a)
		if o == "--parent": parent = int(a)
		if o == "--path": path = str(a)

	if crud == "create":
		if "" in (content, type, parent):
			print "You must supply --content, --type and --parent"
			sys.exit(0)
		print cnt.create(content=content, type=type, parent=parent,
							 label=label, id=id)
	elif crud == "read":
		if path: print cnt.getCPath(path)
		if id: print cnt.read(id)
	elif crud == "tree": tree(cnt, id)
	elif crud == "update":
		if id == 0:
			print "You must supply --id and one of --content, --type, --parent"
			sys.exit(0)
		print cnt.update(id=id, content=content, type=type, parent=parent,
						 label=label)
	elif crud == "delete": print cnt.delete(id)
	elif crud == "deepdelete": print cnt.deepDelete(id)
	else: usage()
	sys.exit(0)

if __name__=="__main__":
	main()

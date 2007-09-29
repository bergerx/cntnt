#!/usr/bin/python

import ply.lex as lex
import ply.yacc as yacc


class MyLexer:
	tokens = (
		'DOT',				# .
		'LABEL', 'TYPE',	# _	 __
		'NAME',				# [A-Za-z0-9-]+
		'LPAREN', 'RPAREN', # ( )
		'EQUAL',			# =
		'AND', 'OR',		# and or
	)
	reserved = {
		'and' : 'AND',
		'or' : 'OR'
	}
	t_DOT = r'\.'
	t_LABEL = r'_'
	t_TYPE = r'__'
	t_LPAREN = r'\('
	t_RPAREN = r'\)'
	t_EQUAL = r'='
	t_ignore = ' \t'
	def t_NAME(self, t):
		r'([A-Za-z0-9-]+)|\*'
		t.type = self.reserved.get(t.value,'NAME')
		return t
	def t_error(self, t):
		print "Illegal char '%s'" % t.value
		t.lexer.skip(1)
	def build(self, **kwargs):
		self.lexer = lex.lex(object=self, **kwargs)
	def test(self, data):
		self.lexer.input(data)
		while 1:
			tok = self.lexer.token()
			if not tok: break
			print tok

# parser bnf

"""
    prefix           : TYPE
                     | LABEL

    prefixedname     : prefix NAME
                     | NAME

    equation         : prefixedname EQUAL NAME

    queryexprunit    : prefixedname
                     | equation

    operator         : AND
                     | OR

    inparen          : queryexprunit operator queryexprunit
                     | queryexprunit

    paren            : LPAREN inparen RPAREN

    branchexpression : prefixedname
                     | paren
                     | prefixedname paren
"""

def p_prefix_type(p):
	'prefix : TYPE'
	p[0] = "__"

def p_prefix_label(p):
	'prefix : LABEL'
	p[0] = "_"

def p_prefixedname_prefix_name(p):
	'prefixedname : prefix NAME'
	p[0] = "%s%s" % (p[1], p[2])

def p_prefixedname_name(p):
	'prefixedname : NAME'
	p[0] = p[1]

def p_equation(p):
	'equation : prefixedname EQUAL NAME'
	p[0] = "%s=%s" % (p[1], p[3])

def p_queryexprunit_prefixedname(p):
	'queryexprunit : prefixedname'
	p[0] = p[1]

def p_queryexprunit_equation(p):
	'queryexprunit : equation'
	p[0] = p[1]

def p_operator_and(p):
	'operator : AND'
	p[0] = "and"

def p_operator_or(p):
	'operator : OR'
	p[0] = "or"

def p_inparen_operator(p):
	'inparen : queryexprunit operator queryexprunit'
	p[0] = "%s %s %s" % (p[1], p[2], p[3])

def p_inparen_queryexprunit(p):
	'inparen : queryexprunit'
	p[0] = p[1]

def p_paren(p):
	'paren  : LPAREN inparen RPAREN'
	p[0] = "(%s)" % p[2]

def p_branchexpression(p):
	'branchexpression : prefixedname'
	p[0] = p[1]

def p_branchexpression(p):
	'branchexpression | paren'
	p[0] = p[1]

def p_branchexpression(p):
	'branchexpression | prefixedname paren'
	p[0] = "%s%s" % (p[1], p[2])

# Error rule for syntax errors
def p_error(p):
	print "Syntax error in input!"



#test = "test.(deneme)"
test = "_basic._views.__view(_name=hede and _type=1).*.__type"


# lexical analyzer
m = MyLexer()
m.build()
m.test(test)


# Build the parser
yacc.yacc()

# Use this if you want to build the parser using SLR instead of LALR
#yacc.yacc(method="SLR")

print yacc.parse(test)

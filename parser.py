#!/usr/bin/python
import ply.lex as lex
import ply.yacc as yacc


# FIXME: Not working
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

def t_NAME(t):
	r'([A-Za-z0-9-]+)|\*'
	t.type = reserved.get(t.value,'NAME')
	return t

def t_error(t):
	print "Illegal char '%s'" % t.value
	lex.skip(1)

def test(data):
	lex.input(data)
	while 1:
		tok = lex.token()
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

    inparen          : queryexprunit AND queryexprunit
                     | queryexprunit OR queryexprunit
                     | queryexprunit

    paren            : LPAREN inparen RPAREN

    branchexpression : prefixedname
                     | paren
                     | prefixedname paren
"""

def p_prefix(p):
	'''prefix : TYPE
			  | LABEL'''
	p[0] = p[1]

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

def p_inparen_operator(p):
	'''inparen : queryexprunit AND queryexprunit
			   | queryexprunit OR queryexprunit'''
	if p[2] == "and":
		p[0] = "%s and %s" % (p[1], p[3])
	elif p[2] == "or":
		p[0] = "%s or %s" % (p[1], p[3])

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
	'branchexpression : paren'
	p[0] = p[1]

def p_branchexpression(p):
	'branchexpression : prefixedname paren'
	p[0] = "%s%s" % (p[1], p[2])

# Error rule for syntax errors
def p_error(p):
	print "Syntax error in input!"

#testCPath = "test.(deneme)"
testCPath = "_basic._views.__view(_name=hede and _type=1).*.__type"

# lexical analyzer
lex.lex()
#test(testCPath)

# Build the parser
yacc.yacc(debug=1)

# Use this if you want to build the parser using SLR instead of LALR
#yacc.yacc(method="SLR")

print yacc.parse(test)

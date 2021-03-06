#!/usr/bin/python
import ply.lex as lex
import ply.yacc as yacc

class ParseError(Exception): pass

# FIXME: Not working
tokens = (
	'DOT',				# .
	'LABELPREFIX',		# _
	'TYPEPREFIX',		# __
	'WORD',				# [A-Za-z0-9]+
	'STAR',				# *
	'LPAREN', 'RPAREN', # ( )
	'EQUAL',			# =
	'AND', 'OR',		# and or
)

reserved = {
	'and' : 'AND',
	'or' : 'OR'
}

t_DOT = r'\.'
t_LABELPREFIX = r'_'
t_TYPEPREFIX = r'__'
t_STAR = r'\*'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_EQUAL = r'='
t_ignore = ' \t\n'

def t_WORD(t):
	r'[A-Za-z0-9]+'
	t.type = reserved.get(t.value,'WORD')
	return t

def t_error(t):
	print "Illegal char '%s'" % t.value
	raise ParseError, "CPath is not valid!"

def lextest(data):
	lex.input(data)
	while 1:
		tok = lex.token()
		if not tok: break
		print tok

# parser
def p_cpath_dot(p):
	'''cpath : cpath DOT branchexpr'''
	p[0] = p[1] + "." + p[3]

def p_cpath(p):
	'''cpath : branchexpr'''
	p[0] = p[1]

def p_branchexpr(p):
	'''branchexpr : name
				  | STAR'''
	p[0] = p[1]

def p_branchexpr_paren(p):
	'''branchexpr : name paren
				  | STAR paren'''
	p[0] = p[1] + p[2]

def p_paren(p):
	'''paren : LPAREN inparen RPAREN'''
	p[0] = "(" + p[2] + ")"

def p_inparen(p):
	'''inparen : equationa'''
	p[0] = p[1]

def p_inparen_operatored(p):
	'''inparen : equationa operator equationa'''
	p[0] = p[1] + " "  + p[2] + " " + p[3]

def p_equation_a(p):
	'''equationa : equation
				 | cpath'''
	p[0] = p[1]

def p_equation(p):
	'''equation : cpath EQUAL cpath'''
	p[0] = p[1] + "=" + p[3]

def p_name(p):
	'''name : WORD
			| type
			| label'''
	p[0] = p[1]

def p_label(p):
	'''type : LABELPREFIX WORD'''
	p[0] = "_" + p[2]

def p_type(p):
	'''label : TYPEPREFIX WORD'''
	p[0] = "__" + p[2]

def p_operator(p):
	'''operator : AND
				| OR'''
	p[0]= p[1]

# Error rule for syntax errors
def p_error(p):
	raise ParseError, "Syntax error in input!"

#testCPath = "test.hede"
#testCPath = "_test.__de(__deneme._h=op and _hoppa.heb=lek).hede"
testCPath = "_basic._views.__view(_name=query and __type=string)._type"
#testCPath = "_basic._views.__view[2]._type" # not supported
#testCPath = "_basic._views.__view(_name=hede and _type=1).*.__type"

debug=0

# lexical analyzer
lex.lex(debug=debug)
#lextest(testCPath)

# Build the parser
yacc.yacc(debug=debug)

# Use this if you want to build the parser using SLR instead of LALR
#yacc.yacc(method="SLR")

try:
	print yacc.parse(testCPath, debug=debug)
except:
	raise ParseError, "CPath does not look valid!"

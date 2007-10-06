#!/usr/bin/python
import ply.lex as lex
import ply.yacc as yacc

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
	lex.skip(1)

def test(data):
	lex.input(data)
	while 1:
		tok = lex.token()
		if not tok: break
		print tok

# parser bnf

"""

_basic._views.__view(_name.__type=query and _type=1).*.__type

TOKENS:
-------
DOT, LABELPREFIX, TYPEPREFIX, WORD, STAR, LPAREN, RPAREN, EQUAL, AND, OR

PARSER BNF:
-----------
type : LABELPREFIX WORD

label : TYPEPREFIX WORD

name : type
	 | label

equation : name EQUAL WORD
		 | cpath equal WORD

inparen : inparen AND cpath
		| inparen OR cpath

paren : LPAREN inparen RPAREN

branchexpr : name
		   | STAR
		   | name paren
		   | STAR paren

cpath : branchexpr DOT cpath | branchexpr
"""

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

def p_equation(p):
	'''equation : name EQUAL WORD
				| cpath EQUAL WORD'''
	p[0] = p[1] + "=" + p[3]

def p_paren(p):
	'''paren : LPAREN inparen RPAREN'''
	p[0] = "(" + p[2] + ")"

def p_inparen_cpath(p):
	'''inparen : cpath'''
	p[0] = p[1]

def p_inparen(p):
	'''inparen : cpath andor cpath'''
	p[0] = p[1] + " "  + p[2] + " " + p[3]

def p_name(p):
	'''name : WORD
			| type
			| label'''
	p[0] = p[1]

def p_type(p):
	'''type : LABELPREFIX WORD'''
	p[0] = "_" + p[2]

def p_label(p):
	'''label : TYPEPREFIX WORD'''
	p[0] = "__" + p[2]

def p_andor(p):
	'''andor : AND
			 | OR'''
	p[0]= p[1]

# Error rule for syntax errors
def p_error(p):
	print "Syntax error in input!"

#testCPath = "test.hede"
testCPath = "_test.__de(__deneme._hop and _hoppa.heblek).hede"
#testCPath = "_basic._views.__view(_name=hede and _type=1).*.__type"

# lexical analyzer
lex.lex(debug=0)
#test(testCPath)

# Build the parser
yacc.yacc(debug=1)

# Use this if you want to build the parser using SLR instead of LALR
#yacc.yacc(method="SLR")

print yacc.parse(testCPath, debug=1)

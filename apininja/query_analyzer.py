from helpers import *
from dis import *
import ast, inspect

def analyze(target):
    if islambda(target):
        analyze_lambda(target)

def analyze_lambda(target):
    code = target.__code__
    print(dir(code))
    
    
l =lambda i: i > 1
def disassemble(co, lasti=-1):
    """Disassemble a code object."""
    code = co.co_code
    labels = findlabels(code)
    n = len(code)
    i = 0
    extended_arg = 0
    free = None
    while i < n:
        op = code[i]

        if i == lasti: print('-->', end=' ')
        else: print('   ', end=' ')
        if i in labels: print('>>', end=' ')
        else: print('  ', end=' ')
        print(repr(i).rjust(4), end=' ')
        print(opname[op].ljust(20), end=' ')
        i = i+1
        if op >= HAVE_ARGUMENT:
            oparg = code[i] + code[i+1]*256 + extended_arg
            extended_arg = 0
            i = i+2
            if op == EXTENDED_ARG:
                extended_arg = oparg*65536
            print(repr(oparg).rjust(5), end=' ')
            if op in hasconst:
                print('(' + repr(co.co_consts[oparg]) + ')', end=' ')
            elif op in hasname:
                print('(' + co.co_names[oparg] + ')', end=' ')
            elif op in hasjrel:
                print('(to ' + repr(i + oparg) + ')', end=' ')
            elif op in haslocal:
                print('(' + co.co_varnames[oparg] + ')', end=' ')
            elif op in hascompare:
                print('(' + cmp_op[oparg] + ')', end=' ')
            elif op in hasfree:
                if free is None:
                    free = co.co_cellvars + co.co_freevars
                print('(' + free[oparg] + ')', end=' ')
            elif op in hasnargs:
                print('(%d positional, %d keyword pair)'
                      % (code[i-2], code[i-1]), end=' ')
        print()
disassemble(l.__code__)
source = inspect.getsource(l)
print(source)
print(ast.parse(source))

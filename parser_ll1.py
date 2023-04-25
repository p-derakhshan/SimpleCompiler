__author__ = " Parya Derakhshan "

import numpy as np
from collections import OrderedDict
from inout import Error,Log

EPSILON = '~'
START,END='START','EOF'
ACCEPT,ERROR,POP='ACCEPT','ERROR','POP'
errors = {
    'll1':'GrammarError',
    'prsr':'ParserError [LL1]'
}

class LL1():
    def __init__(self,grammar):
        self.productions, self.variables, self.terminals = self.read_grammar(grammar)
        self.terminals.remove(EPSILON)
        self.symbols = self.variables+self.terminals
        self.epsilons = self.mark_epsilon()
        self.first(),self.follow()

    def components(self):
        return self.symbols,self.terminals, self.First, self.Follow

    def read_grammar(self,lines): #read grammar.txt and sets terminals,variables and rules
        if len(lines)==0: Error().parser(errors['ll1'],'Grammar Not Found')
        productions,productions_all=OrderedDict(()),OrderedDict(())
        variables,terminals,words = [],[],[]
        for i in range(len(lines)):
            line = lines[i]
            line.strip()
            left,right = line.split('->')
            left = left.replace(' ','')
            if not left in variables: variables.append(left)
            key = str(i)+'.'+left
            productions_all[key]=[]
            for r in right.split(' '):
                r= r.strip()
                if r.isspace() or not r: continue 
                if r ==EPSILON : productions_all[key]=r[0]
                else: productions_all[key].append(r)
                words.append(r)
        for w in words: 
            if w not in terminals and w not in variables: terminals.append(w)
        for v in variables:
            productions[v]=[]
            for key,value in productions_all.items():
                if value[0]==EPSILON: value=value[0]
                if key.split('.')[1]==v: productions[v].append(value)
        self.rules = productions_all
        return productions,variables,terminals

    def mark_epsilon(self): #marking algorithm for variables that can drive epsilon
        marked = []
        variables = self.variables
        for v in variables:
            derivations = self.productions[v]
            if EPSILON in derivations: marked.append(v)
        for i in range(len(variables)):
            v = variables[i]
            if v in marked: continue
            derivations = self.productions[v]
            for der in derivations:
                all_marked =True
                for s in der:
                    if (s in self.terminals) or (s not in marked):
                        all_marked = False
                        break
                if all_marked: 
                    i = 0
                    marked.append(v)
                    break
        return marked
    
    def relation_F(self): # relation F for First (matrix output)
        n = len(self.symbols)
        f1 = np.full((n, n), 0)
        for v in self.variables:
            i = self.symbols.index(v)
            derivations = self.productions[v]
            for der in derivations:
                if der[0] == EPSILON: continue
                j = self.symbols.index(der[0])
                if f1[i,j]==1: return Error().parser(errors['ll1'],'Condition I')
                f1[i,j]=1
        F, F_sum=[f1], f1
        while(F[-1].any()):
            f_p = np.linalg.matrix_power(f1,(len(F)+1))
            F.append(f_p)
            F_sum = np.add(F_sum,f_p)
            if F_sum.max()>1: return Error().parser(errors['ll1'],'Condition I')
        self.F = F_sum
            
    def first(self): # First for variables (dictionary output)
        self.relation_F()
        self.First = {}
        n_v = len(self.variables)
        for i in range(n_v):
            v = self.variables[i]
            self.First[v]=[]
            row =self.F[i,n_v:]
            for j in range(len(row)):
                if row[j]: self.First[v].append(self.terminals[j])
            if v in self.epsilons: 
                self.First[v].append(EPSILON)

    def relation_L(self): # relation L for Last (matrix output)
        n = len(self.symbols)
        l1 = np.full((n, n), 0)
        for v in self.variables:
            i = self.symbols.index(v)
            derivations = self.productions[v]
            for der in derivations:
                if der[-1] == EPSILON or der[-1]==v: continue
                j = self.symbols.index(der[-1])
                l1[i,j]=1
        L,L_sum=[l1],l1
        while(L[-1].any()):
            l_p = np.linalg.matrix_power(L[0],(len(L)+1))
            L.append(l_p)
            L_sum = np.add(L_sum,l_p)
        self.L=L_sum
    
    def relation_B(self): # relation B for Beside (matrix output)
        n= len(self.symbols)
        B_sum = np.full((n, n), 0)
        for derivations in list(self.productions.values()):
            for der in derivations:
                b1 = np.full((n, n), 0)
                if len(der)<2: continue
                for k in range(1,len(der)):
                    left,right = der[k-1],der[k]
                    i,j =self.symbols.index(left),self.symbols.index(right)
                    b1[i,j]=1
                B_sum = np.add(B_sum,b1)
        self.B = B_sum

    def follow(self): # Follow for variables (dictionary output)
        self.relation_L()      
        self.relation_B()
        n,n_v = len(self.symbols),len(self.variables)
        self.Follow,flws={},{}
        L,B,F = self.L,self.B,self.F
        for i in range(len(self.symbols)):
            L[i,i],F[i,i]=1,1
        L_t = L.transpose()
        temp = np.matmul(B, F)
        follow = np.matmul(L_t,temp) #Follow = L_transpose*B*F
        for i in range(n_v):
            v = self.variables[i]
            self.Follow[v],flws[v]=[],[]
            row =follow[i,:]
            for j in range(n):
                if row[j]: 
                    flws[v].append(self.symbols[j])
                    if j>=n_v:self.Follow[v].append(self.symbols[j])
        for v,flw in flws.items():
            for f in flw: 
                if f in self.variables:
                    t = list(set(self.Follow[v]+self.Follow[f]))
                    self.Follow[v]=t
        for v in self.epsilons:
            intersection = list(set(self.First[v]) & set(self.Follow[v]))
            if intersection: return Error().parser(errors['ll1'],'Condition II: '+v+'->'+str(intersection))

    def first_index(self,var,symbol): # index)variable->derivation : symbol in First(derivation)
        for key,der in self.rules.items():
            index,variable = key.split('.')
            if variable == var:
                remaining = der
                while remaining:
                    s = remaining[0]
                    if not s in self.variables:
                        if s == symbol: return (der,index)
                        else: break
                    else:
                        if symbol in self.First[s]: return (der,index)
                        if not s in self.epsilons: break
                        else: del remaining[0]
        return ERROR

class Parser():
    def __init__(self):
        self.stack,self.rules=[END,START],[]
    
    def creat_table(self,grammar):
        self.grammar = LL1(grammar)
        self.symbols,self.terminals,self.firsts,self.follows = self.grammar.components()
        self.table=self.parsing_table()
        return self.table_output()

    def parsing_table(self): #create parse table according to the grammar
        table = {}
        for i in range(len(self.symbols)):
            symbol=self.symbols[i]
            table[symbol]={}
            for terminal in self.terminals: table[symbol][terminal]=ERROR
            if symbol in self.terminals:
                if symbol!=END: table[symbol][symbol]=POP
                else: table[symbol][symbol]= ACCEPT
            else:
                first_v=self.firsts[symbol]
                for first in first_v:
                    rule= self.grammar.first_index(symbol,first)
                    if first!=EPSILON: table[symbol][first]= rule
                    else: 
                        follow = self.follows[symbol]
                        not_first= [flw for flw in follow if flw not in first_v]
                        for flw in not_first: table[symbol][flw]= rule                
        return table
 
    def table_output(self):
        txt = []
        txt.append('{:15s}'.format(' ')+' | ')
        for t in self.terminals:  txt.append('{:45s}'.format(t)+' | ')
        txt.append('\n'+('_'*(len(self.terminals)*48+18))+'\n')
        for s in self.symbols:
            txt.append('{:15s}'.format(s)+' | ')
            for t,d in self.table[s].items():
                if d not in [ACCEPT,ERROR,POP]: 
                    d = '('+self.get_der(d[0])+','+d[1]+')'
                txt.append('{:45s}'.format(str(d))+' | ')
            txt.append('\n'+('_'*(len(self.terminals)*48+18))+'\n')   
        txt.pop(-1)
        return txt

    def get_der(self,rule):
        der = ''
        for symbol in rule: der+= (symbol+' ')
        return der.strip()

    def parse_tokens(self,tokens): #read tokens.txt
        if len(tokens)==0: return Error().parser(errors['prsr'],'Tokens Not Found')
        symbols=[]
        for token in tokens:
            code,const = token.split(EPSILON)
            symbols.append(const.strip())
        symbols.append(END)
        result = self.parse(symbols)
        if result==ERROR: 
            self.rules.append('<Production Rule Not Found>')
            Error().parser(errors['prsr'],'Invalid Command')
        else: Log().success('Program Was Parsed Successfully [LL1]')
        return self.rules
   
    def get_rule(self,number,var,rule):
        return number+') '+var+' -> '+self.get_der(rule)+'\n'

    def parse(self,tokens): #parse tokens according to the parse table
        while tokens:
            A ,a = self.stack[-1],tokens[0]
            if not a in self.symbols: return ERROR
            M = self.table[A][a]
            if M ==POP: 
                del tokens[0]
                self.stack.pop(-1)
            elif M ==ACCEPT: return self.rules 
            elif M==ERROR: return ERROR
            else:
                rule,number = M
                self.stack.pop(-1)
                if rule!=EPSILON:
                    for s in reversed(rule): self.stack.append(s)
                self.rules.append(self.get_rule(number,A,rule))
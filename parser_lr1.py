__author__ = " Parya Derakhshan "

import numpy as np
from collections import OrderedDict
from inout import Error,Log

EPSILON = '~'
START,END='START','EOF'
ACCEPT,ERROR,POP='ACCEPT','ERROR','POP'
errors = {
    'll1':'GrammarError',
    'prsr':'ParserError [LR1]'
}

class Item(): # variable --> [completed] . [expected] , [lookahead]
    def __init__(self, variable, completed, expected, lookahead):

        '''handle epsilon line an empty symbol'''
        if completed == EPSILON: completed=[] 
        if expected == EPSILON: expected=[] 
        if lookahead == EPSILON: lookahead=[] 
        if EPSILON in completed: completed.remove(EPSILON)
        if EPSILON in expected: expected.remove(EPSILON)

        self.lookahead=[]
        for l in lookahead:
            if l == EPSILON or l==[]: continue
            '''delete repeates from lookahead'''
            if not l in self.lookahead: self.lookahead.append(l)

        self.variable,self.completed,self.expected=variable, completed, expected

    def same_rule(self, item):
        '''check if variable --> completed . expected are the same'''
        return self.variable==item.variable and self.completed==item.completed and self.expected==item.expected

    def equal(self,item):
        '''check if items are the same'''
        return self.same_rule(item) and self.lookahead==item.lookahead

    def print_item(self):
        '''return( variable --> completed . expected , lookahead)'''
        return '{}-->{}.{},{}'.format(self.variable, self.completed, self.expected, self.lookahead)

class State(): # header:item, closure:[items], edge:[(label,state)], id: int
    count=0 #state id
    def __init__(self, item):
        self.header = item
        self.closure, self.edge = [], []
        self.id = State.count
        State.count+=1

    def add_node(self,symbol,state):
        '''add (label,neighbor) to edge'''
        self.edge.append((symbol,state))
    
    def add_closure(self, item):
        '''add new closure item if it doesn't already exist'''
        for c in self.closure:
            if item.same_rule(c):
                '''if there's an item in the closure with different lookaheads just update lookaheads'''
                tmp = c.lookahead+item.lookahead
                c.lookahead = list(set(tmp))
                return True
        self.closure.append(item)

    def get_edges(self):
        '''get neighbor states based on the first symbol in [expected]'''
        header,closures=self.header, self.closure
        if not header.expected: return[] #leaf
        edges, items = [], ([header] + closures)
        for item in items:
            if len(item.expected)>0:
                tmp = item.completed + [item.expected[0]]
                item_new = Item(item.variable,tmp,item.expected[1:],item.lookahead)
                edges.append((item.expected[0],item_new))
        return edges
    
    def print_state(self):
        '''return id, header, number of edges'''
        r =('{}) \n\t{}\t:{} edges\n{}'.format(self.id,self.header.print_item(),len(self.edge),('_'*20)))
        '''return closure items'''
        for i in self.closure:
            r+=('{}\n\n'.format(i.print_item()))
        r+=('\n'*2)
        return r   

class LR1():
    def __init__(self,grammar):
        self.productions, self.variables, self.terminals = self.read_grammar(grammar)
        if EPSILON in self.terminals: self.terminals.remove(EPSILON)
        self.symbols = self.variables+self.terminals
        self.epsilons = self.mark_epsilon()
        self.firsts = self.first()
        self.automata = self.graph()

    def components(self):
        return self.symbols,self.variables, self.automata, self.rules

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
    
    def relation_F(self): # relation F for firsts (matrix output)
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
            
    def first(self): # firsts for variables (dictionary output)
        self.relation_F()
        first = {}
        n_v = len(self.variables)
        for i in range(n_v):
            v = self.variables[i]
            first[v]=[]
            row =self.F[i,n_v:]
            for j in range(len(row)):
                if row[j]: first[v].append(self.terminals[j])
            if v in self.epsilons: 
                first[v].append(EPSILON)
        return first

    def rule_index(self,var,der): # index)variable->derivation
        '''get rule index based on the variable and derivations in it'''
        for key,derivation in self.rules.items():
            index,variable = key.split('.')
            if variable == var and derivation==der: return index
        return ERROR

    def rule_derivation(self,i): # index)variable->derivation
        '''get rule's variable and derivations based on its index'''
        for key,derivation in self.rules.items():
            index,variable = key.split('.')
            if index == i: return variable, derivation
        return ERROR

    def expected_lookahead(self, expected, lookahead):
        '''for item with .[expected],[lookahead] returns closures:[(var,lookaheads)]'''

        '''leaf with no closure'''
        if not expected or expected[0] in self.terminals:  return 0

        '''no additional lookahead and just one variable'''
        if len(expected)==1: return[(expected[0],lookahead)]

        '''add the first expected variable and all possible lookaheads'''
        firsts=[(expected[0],self.lookahead(expected[1:],lookahead))]

        '''check for epsilon driven variables after the first expected symbol'''
        if expected[0] in self.epsilons:
            follow = self.expected_lookahead(expected[1:],lookahead)
            if follow: firsts += follow

        return firsts

    def lookahead(self,expected,lookahead):
        '''for item with .[expected[1:]],[lookahead] returns [lookaheads]'''

        '''leaf with no closures'''
        if not expected: return []

        '''the first symbol is a terminal'''
        if expected[0] in self.terminals: return [expected[0]]

        '''add the first variables firsts'''
        firsts, reach_end = self.firsts[expected[0]], True
        
        '''check for epsilon driven variables after the first expected variable'''
        if expected[0] in self.epsilons and len(expected)>1: 
            follow = self.lookahead(expected[1:],lookahead)
            if follow: firsts+=follow

        '''if all the variables in expected and drive epsilon also add the original lookahead'''
        for e in expected:
            if not e in self.epsilons:
                reach_end=False
                break
        if reach_end: firsts+=lookahead

        return firsts

    def state_closures(self,state):
        '''calculate state's closure items'''

        '''state's header item'''
        header, check = state.header, []

        '''header's directly deriven closure items'''
        items = self.expected_lookahead(header.expected, header.lookahead) 
        if items ==0: return state #no closure items
        for var,lookahead in items:
            for derivation in self.productions[var]:
                new_item = Item(var,[],derivation,lookahead)
                if not new_item in state.closure: 
                    state.add_closure(new_item)
                    check.append(new_item)

        '''closure items driven from unchecked closure items in the state'''
        while check:
            item = check.pop(0)
            items = self.expected_lookahead(item.expected, item.lookahead) 
            if items == 0: continue
            for var,lookahead in items:
                for derivation in self.productions[var]:
                    new_item = Item(var,[],derivation,lookahead)
                    if not new_item in state.closure: 
                        state.add_closure(new_item)
                        check.append(new_item)

        return state

    def graph(self):
        '''parser's NFA'''
        automata ={}
        
        '''initial state: id0)ZERO-->[],START,EOF'''
        state0 = State(Item('ZERO', [], ['START'], ['EOF']))
        automata[state0.id]=state0

        '''create all possible states'''
        id=0
        while id<State.count:

            '''calculate closures based on the header'''
            state = self.state_closures(automata[id])

            '''claculate (edge,neighbor) based on first expected symbol'''
            edges= state.get_edges()

            for edge,item in edges:

                '''check if a state with similar header item doesn't already exist'''
                check,i=True,0
                for k, s in automata.items():
                    if s.header.equal(item): 
                        check,i=False,s.id
                        break
                '''create new neighboring state'''
                if check:
                    state_new = State(item)
                    i= state_new.id
                    automata[i]=state_new

                '''add state's edges'''
                if (edge,i) not in state.edge: state.edge.append((edge,i))

            id+=1
        return automata

class Parser():
    def __init__(self):
        self.stack,self.output=[0],[]
    
    def table_automata(self,grammar):
        self.grammar = LR1(grammar)
        self.symbols,self.variables,self.automata,self.productions = self.grammar.components()
        self.table=self.parsing_table( self.symbols,self.variables,self.automata)
        return self.table_output()

    def parsing_table(self,symbols,variables,automata):
        table,self.ids = {},[]
        '''table[id][terminal-variable]'''
        for id, state in automata.items():
            self.ids.append(id)
            table[id]={}
            for symbol in symbols: table[id][symbol]=ERROR
            for edge, node in state.edge:
                if edge in variables: table[id][edge]=('G',node) #GoTo
                else: table[id][edge]=('S',node) #shiftTo
            items = [state.header]+state.closure
            for item in items:
                if not item.expected:  #leaf or epsilon derivation
                    var,der = item.variable, item.completed
                    if not item.completed: der = EPSILON
                    elif item.lookahead == [END] and item.completed==[START]: 
                        for s in symbols: table[id][s]=ACCEPT
                        self.accept_id = id
                        continue
                    index = self.grammar.rule_index(var,der)
                    for terminal in item.lookahead:
                        table[id][terminal]=('R',index) #ReduceTo
        return table

    def table_output(self):
        txt = []
        txt.append('{:4s}'.format(' '))
        for symbol in self.symbols: txt.append('|{:11s}'.format(symbol))
        txt.append('\n'+'_'*(4+12*len(self.symbols))+'\n')
        for id in self.ids:
            txt.append('{:4.0f}'.format(id))
            for symbol in self.symbols: 
                txt.append('|{:11s}'.format(str(self.table[id][symbol])))
            txt.append('\n'+'_'*(4+12*len(self.symbols))+'\n')
        return txt

    def automata_output(self):
        txt=[]
        for id, state in self.automata.items():
            txt.append(state.print_state())
        return txt

    def parse_tokens(self,tokens): #read tokens.txt
        if len(tokens)==0: return Error().parser(errors['prsr'],'Tokens Not Found')
        symbols=[]
        for token in tokens:
            code,const = token.split(EPSILON)
            symbols.append(const.strip())
        symbols.append(END)
        result = self.parse(symbols)
        if result==ERROR: 
            self.output.append('<Production Rule Not Found>')
            Error().parser(errors['prsr'],'Invalid Command')
        else: Log().success('Program Was Parsed Successfully [LR1]')
        self.output.reverse()
        return self.output
   
    def get_rule(self,number,var,rule):
        der = ''
        for symbol in rule: der+= (symbol+' ')
        return number+') '+var+' -> '+der.strip()+'\n'

    def parse(self,tokens): #parse tokens according to the parse table
        while tokens:
            A ,a = self.stack[-1],tokens[0]
            if A in self.variables: #GoTo
                A2 = self.stack[-2]
                M = self.table[A2][A]
                if not type(M) is tuple or not M[0] =='G': return ERROR
                self.stack.append(M[1])
            elif A in self.ids:
                M = self.table[A][a]
                if M== ACCEPT: return self.output
                if not type(M) is tuple: return ERROR
                instruction, id = M
                if instruction not in ['R','S']: return ERROR
                if instruction=='S': #ShifTo
                    del tokens[0]
                    self.stack.append(a)
                    self.stack.append(id)
                else: #ReduceTo
                    variable, derivation = self.grammar.rule_derivation(id)
                    if derivation!=EPSILON: 
                        for i in range(len(derivation)-1,-1,-1):
                            if self.stack[-2]!= derivation[i]: return ERROR
                            self.stack.pop(-1)
                            self.stack.pop(-1)
                    self.stack.append(variable)
                    self.output.append(self.get_rule(id,variable,derivation))
            else: return ERROR

def run(files,dir_grammar,dir_parsetable,dir_automata,dir_tokens,dir_rules):
    '''read grammar and calculate first and automata'''
    grammar = files.set_directory(dir_grammar,dir_parsetable)
    parser = Parser()
    '''calculate and print parsing table'''
    table = parser.table_automata(grammar)
    files.write(table)
    files.close()
    '''print automata'''
    f = files.set_directory(dir_grammar,dir_automata)
    files.write(parser.automata_output())
    files.close()
    '''read tokens and parse the program'''
    tokens = files.set_directory(dir_tokens,dir_rules)
    rules = parser.parse_tokens(tokens)
    '''print rules'''
    files.write(rules)
    files.close()

if __name__ == "__main__":
    from inout import File

    dir_program = 'program.txt'
    vis,outs = 'visualizations','outputs'
    files = File(dir_program,[vis,outs])

    dir_tokens, dir_grammar, dir_rules_lr1 = (outs+'/tokens.txt'),'grammar.txt', (outs+'/rules_lr1.txt')
    dir_parsetable_lr1, dir_automata =(vis+'/parsetable_lr1.txt'), (vis+'/automata.txt')
    
    run(files,dir_grammar,dir_parsetable_lr1,dir_automata,dir_tokens,dir_rules_lr1)

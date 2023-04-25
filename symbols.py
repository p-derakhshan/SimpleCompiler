__author__ = " Parya Derakhshan "

from collections import OrderedDict
class SymbolTable():
    
    def __init__(self):
        '''create 3 ordered dictionaries'''
        self.rw = self.create_reservedwords()
        self.dl_op = self.create_delimiters_operators()
        self.id = OrderedDict()
        '''join the dictionaries'''
        self.table = {**self.rw, **self.dl_op, **self.id}
    
    def create_reservedwords(self):
        rw = OrderedDict((('Loop','LOOP'), ('Until','UNTIL'),
                          ('Str','STR'), ('Num','NUM'), ('Flt','FLT'),
                          ('Condition','CONDITION'), ('Block','BLOCK'),
                          ('Array','ARRAY'), ('Begin','BEGIN'),
                          ('End','END')))
        return rw  
    
    def create_delimiters_operators(self):
        dl_op = OrderedDict((('|','EOL'), ('%','SL_COMMENT'),
                             ('%%','ML_COMMENT'), ('*','MUL'), ('/','DIV'),
                             ('+','ADD'), ('-','SUB'), ('//','REMAINDER'), 
                             ('(','LP'), (')','RP'), ('[','LB'), (']','RB'), 
                             ('\"','DQUOTE'), (':=','ASGN'), ('==','EQL'), 
                             ('>=','GREATER_EQL'), ('<=','SMALLER_EQL'), 
                             ('>','GREATER'), ('<','SMALLER')))
        '''get charchters of each sumbol'''
        temp1,temp2 = [],[]
        for key in list(dl_op.keys()):
            if len(key)>1: temp2.append(key)
            if key[0] not in temp1: temp1.append(key[0])
        temp1.remove('%'), temp2.remove('%%')
        self.CH1 , self.CH2= temp1,temp2
        #operators with 2 characters :  //,==,<=,>=
        return dl_op
                
    def get_pattern_code(self,key):
        if key in self.rw: return'RW'
        elif key in self.dl_op: return'DL-OP'
        elif key in self.id: return 'ID'
        else: return 'Not Found'
    
    def get_lexeme_code(self, table, key):
        if table == 'ST':table = self.get_pattern_code(key)
        if table == 'RW' and key in self.rw: return self.rw[key]
        elif table == 'DL-OP' and key in self.dl_op: return self.dl_op[key]
        elif table == 'ID' and key in self.id: return key
        else: return -1

    def insert_var(self, name):
        index = len(self.table) #index in the table
        self.id[name],self.table[name] = index ,index
        return index #added varibales index in symbol table

    def table_output(self): #write symbol table into symboltable.txt
        t,i =('_' * 44),0
        txt = ('_'*16)+'SYMBOLTABLE'+('_'*16)+'_\n'
        txt+="{:<6} | {:<15} | {:<15}\n{:s}\n".format('Index','Lexeme Code','Constant',t)
        for k,v in self.table.items():
            if i==10 or i ==29: txt+=(t+'\n')
            txt+=("{:<6} | {:<15} | {:<15}\n".format(i,k, v))
            i+=1
        return txt


class Charachter():
    def __init__(self,CH1,CH2):
        self.DIGITS = ['0','1','2','3','4','5','6','7','8','9']
        self.DOT = '.'
        self.QUOTE = '\"'
        self.SYMBOLS1 = CH1
        self.SYMBOLS2 = CH2  #dl_op with 2 characters
        self.PERCENT = '%'
        self.WHITE_SPACE = [' ','\t']
        self.VERTICAL_BAR = '|'
        self.COLON = ':'
        self.EQL = '='
    
    def is_white_space(self, char):
        return (char in self.WHITE_SPACE)
    
    def is_dot(self, char):
        return (char == self.DOT)
    
    def is_quote(self, char):
        return (char == self.QUOTE)
    
    def is_percent(self, char):
        return (char == self.PERCENT)
    
    def is_symbol(self, char):
        return (char in self.SYMBOLS1)
    
    def is_symbol_2digits(self, str):
        return (str in self.SYMBOLS2)
    
    def is_digit(self, char):
        return (char in self.DIGITS)
    
    def is_letter(self, char):
        return (char.isalpha()) #if it is an alphabet or not
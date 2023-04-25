__author__ = " Parya Derakhshan "

from inout import Error, Log

EPSILON = '~'
ERROR = { 'EOF':'EOF while scanning',
        'EOL': 'EOL while scanning',
        'VAR':'invalid variable',
        'FORMAT': 'invalid format',
        'SYNTAX': 'invalid syntax',
        'CH': 'invalid charachter'}

class Token():
    def __init__(self, value):
        self.value = value
        
    def set_code(self, pattern, lexeme):
        '''set token values'''
        self.pattern_code= pattern  
        self.lexeme_code= lexeme
        
    def tokenize(self):
        return ('%s~%s' %(self.pattern_code, self.lexeme_code))       

class Scanner():
    def __init__(self,program,symbol_table,CH,file):
        self.tokens = []#all tokens in the program
        self.closed_comment = True#no open multiline comment
        self.line_number = 0 #current line's number
        self.ST,self.CH,self.F = symbol_table,CH,file
        self.lines,self.line_full=program,''
        self.next_line()
    
    def close(self):
        self.F.write(self.tokens_output())
        self.F.close()
        import main
        main.write_symbol_table(self.F,self.ST)
        main.parse(self.F)
        quit()

    def get_line(self): #first line in remaining lines
        line = self.lines[0]
        del(self.lines[0])
        return line

    def tokens_output(self):
        txt =''
        for token in self.tokens: txt+=(token+'\n')
        return txt

    def error(self, err_type, err_value):#print error in the console then exit
        return Error().scanner(self.line_number,ERROR[err_type], err_value)
        
    def next_line(self): #read next line and its first charachter and scan it
        self.read_line()
        self.read_char()
        self.scan()

    def read_line(self):
        if len(self.lines)>0: #line has next
            line = self.get_line() #read the current line from input file
            self.line_number+=1 #update current line number
            #skip if it's empty
            if line =='\n': return self.read_line()
            #remove \n from the end of each line
            if line[-1]=='\n': line = line[0:-1]
            '''update current line'''
            self.current_line,self.line_full= line,line
            return line
        else: #reached the end of the file
            if not self.closed_comment:return self.error('EOF','%%')   
            Log().success('Program Was Scanned Successfully')
            return self.close()
        
    def line_has_next(self):
        if not len(self.current_line): return False
        for c in self.current_line:
            if not self.CH.is_white_space(c): return True
        return False
    
    def read_char(self):
        line = self.current_line
        if len(line)>0:    
            ch,self.current_char = line[0],line[0]
            self.current_line=line[1:]
            if ch ==EPSILON: return self.error('CH',EPSILON)
            return ch
        else:
            if not self.closed_comment:
                self.read_line()
                return self.read_char()
            return self.next_line()
    
    def tokenize_var_number(self, value): #tokenize numbers (integer/float)
        token = Token(value)
        if value.isdigit(): #if it consists of only digits --> integer
            pattern_code,lexeme_code=int(value),'VAR_INT'
        else: #if it has "." --> float
            pattern_code,lexeme_code=float(value),'VAR_FLOAT'
        token.set_code(pattern_code, lexeme_code)
        return self.tokens.append(token.tokenize())
        
    def tokenize_var_string(self, value): #tokenize strings
        token = Token(value)
        pattern_code,lexeme_code = value,'VAR_STRING'
        token.set_code(pattern_code, lexeme_code)
        return self.tokens.append(token.tokenize())
                              
    def tokenize_word(self, value): #tokenize reserved words and vaiables(ID)
        token = Token(value)
        pattern_code=self.ST.get_pattern_code(value)
        if pattern_code=='RW' or pattern_code=='ID': #it exists in symbol table
            lexeme_code=self.ST.get_lexeme_code(pattern_code,value)
            if pattern_code=='ID':
                pattern_code=lexeme_code
                lexeme_code='ID'
        else: #add to symbol table as ID
            #invalid variable name
            if value[0:3]!='var' or not value[3:].isdigit(): return self.error('FORMAT',value)
            # pattern_code='ID'
            lexeme_code = self.ST.insert_var(value)
            pattern_code,lexeme_code=value,'ID'
        token.set_code(pattern_code, lexeme_code)
        return self.tokens.append(token.tokenize())
        
    def tokenize_dl_op(self,value): #tokenize delimiters and operators
        token = Token(value)
        pattern_code,lexeme_code = 'DL-OP',self.ST.get_lexeme_code('DL-OP',value)
        if lexeme_code==-1: return self.error('SYNTAX',value)
        token.set_code(pattern_code, lexeme_code)
        return self.tokens.append(token.tokenize())

    def skip_comment_ml(self): #skip multiline comment
        self.closed_comment = False
        ch = self.current_char
        while not self.CH.is_percent(ch): ch = self.read_char()
        ch = self.read_char()
        if self.CH.is_percent(ch): #end of the comment
            self.closed_comment = True
            self.tokenize_dl_op('%%')
            #invalid code written in the same line as the end of the comment
            if len(self.current_line)>0: return self.error('SYNTAX',self.current_line)
            return self.next_line()
        else: return self.skip_comment_ml()
    
    def scan(self):
        ch,word= self.current_char,''
        if  self.CH.is_white_space(ch): #skip white spaces
            self.read_char()
            return self.scan()
        
        elif self.CH.is_digit(ch): #number 
            end_line = False
            while self.CH.is_digit(ch):
                word+=ch
                if not self.line_has_next():
                    end_line=True
                    break
                ch = self.read_char()
            if self.CH.is_dot(ch):
                word+=ch
                #line can't end with digit
                if not self.line_has_next(): return self.error('FORMAT',word)
                ch = self.read_char()
                #there should be digits after . in numbers
                if not self.CH.is_digit(ch): return self.error('FORMAT',word)
                while self.CH.is_digit(ch):
                    word+=ch
                    if not self.line_has_next():  break
                    ch = self.read_char()
            self.tokenize_var_number(word)
            if end_line: return self.next_line()
            return self.scan()
        
        elif self.CH.is_quote(ch): #string
            word +=ch
            #there should be something after " in the line
            if not self.line_has_next(): return self.error('EOL','string literal (\")')
            ch = self.read_char()
            while not self.CH.is_quote(ch):
                word +=ch
                #the string wasn't closed untill the end of the line
                if not self.line_has_next(): return self.error('EOL','string literal (\")')
                ch = self.read_char()
            word+=ch
            self.tokenize_dl_op('\"')
            self.tokenize_var_string(word[1:-1])
            self.tokenize_dl_op('\"')
            if not self.line_has_next(): return self.next_line()
            self.read_char()
            return self.scan()
        
        elif self.CH.is_percent(ch): #comment
            ch = self.read_char()
            if self.CH.is_percent(ch): #multiline comment
                self.read_char()
                return self.skip_comment_ml()
            else: #singleline comment
                self.tokenize_dl_op('%')
                #skip the whole line
                if self.line_has_next(): return self.next_line()
                return self.scan()
        
        elif self.CH.is_symbol(ch): #delimiter-operator
            word = ch
            end_line = not self.line_has_next()
            if not end_line: 
                # "|" can appear only at the end of the line'''
                if ch == self.CH.VERTICAL_BAR: self.error('SYNTAX',('|' +self.current_line))
                ch = self.read_char()
                if self.CH.is_symbol_2digits((word+ch)): #check if dl_op can have 2 symbols
                    word +=ch
                    ch = self.read_char()
            self.tokenize_dl_op(word)
            if end_line: return self.next_line()
            return self.scan()       
        
        elif self.CH.is_letter(ch): #letter
            end_line = False
            while self.CH.is_letter(ch):
                word+=ch
                if not self.line_has_next(): 
                    end_line=True
                    break
                ch = self.read_char()
            #there can be digits after letters in variable names
            while self.CH.is_digit(ch):
                word+=ch
                if not self.line_has_next(): 
                    end_line=True
                    break
                ch = self.read_char()
            self.tokenize_word(word)
            if end_line: return self.next_line()
            return self.scan()     
        
        else: #error (otherwise)
            return self.error('SYNTAX',ch)
        

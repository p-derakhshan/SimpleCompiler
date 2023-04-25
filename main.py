__author__ = " Parya Derakhshan "

'''main->scanner->symbol table->grammar->parser'''

from inout import File
from symbols import SymbolTable,Charachter

dir_program = 'program.txt'
vis,outs = 'visualizations','outputs'

dir_tokens,dir_symboltable = (outs+'/tokens.txt'),(vis+'/symboltable.txt')
dir_grammar, dir_parsetable_ll1 = 'grammar.txt',(vis+'/parsetable_ll1.txt')
dir_parsetable_lr1, dir_automata =(vis+'/parsetable_lr1.txt'), (vis+'/automata.txt')
dir_rules_ll1, dir_rules_lr1 = (outs+'/rules_ll1.txt'),(outs+'/rules_lr1.txt')


def parse(files):
    '''Grammar'''
    from parser_ll1 import Parser
    grammar = files.set_directory(dir_grammar,dir_parsetable_ll1)
    parser = Parser()
    table = parser.creat_table(grammar)
    files.write(table)
    files.close()
    '''Parser LL1'''
    tokens = files.set_directory(dir_tokens,dir_rules_ll1)
    rules = parser.parse_tokens(tokens)
    files.write(rules)
    files.close()
    '''Parser LR1'''
    from parser_lr1 import run
    run(files,dir_grammar,dir_parsetable_lr1,dir_automata,dir_tokens,dir_rules_lr1)

def write_symbol_table(files,ST):
    '''Symbol Table'''
    program = files.set_directory(dir_program,dir_symboltable)
    files.write(ST.table_output())
    files.close()

def scan(files,ST,CH):
    '''Scanner'''
    from scanner import Scanner
    program = files.set_directory(dir_program,dir_tokens)
    scanner = Scanner(program,ST,CH,files)

if __name__ == '__main__':
    files = File(dir_program,[vis,outs])
    ST = SymbolTable()
    CH = Charachter(ST.CH1, ST.CH2)
    scan(files,ST,CH)

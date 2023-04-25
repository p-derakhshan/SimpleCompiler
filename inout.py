__author__ = " Parya Derakhshan "

import os
import sys

class Colors:
    RED = '\033[31m'
    ENDC = '\033[m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'

class Log(): #print in console
    def err(self,err): #red
        print(Colors.RED  + err + Colors.ENDC)

    def success(self,value): #green
        print(Colors.CYAN+ value + Colors.ENDC)

    def info(self,value): #blue
        print(Colors.BLUE + value + Colors.ENDC)

    def warn(self,value): #yellow
        print(Colors.YELLOW + value + Colors.ENDC)

class Error(): #handle errors
    def file(self, err_type, err_value, path):
        txt = '{:s}: \'{:s}\'\At Path {:s}'.format(err_type,err_value,path)
        Log().err(txt)
        sys.exit()

    def scanner(self, line_number, err_type, err_value):
        txt = 'Program Exited At Line {:.0f}\nSyntaxError: {:s} {:s}'.format(line_number,err_type,err_value)
        Log().err(txt)
        sys.exit()

    def parser(self,err_type,err_value):
        txt = '{:s}: {:s}'.format(err_type,err_value)
        Log().err(txt)
    

class File(): #read-write files
    def __init__(self,dir_in,dir_out):
        if not os.path.exists(dir_in):
            '''can't find program's file'''
            path = os.path.realpath('.')
            Error().file('FileNotFound',dir_in,path)
            sys.exit()
        '''set file paths'''
        for directory in dir_out:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def set_directory(self,dir_in,dir_out): #open files
        self.file_in = open(dir_in, 'r')
        self.file_out = open(dir_out, 'w')
        self.lines = self.read_lines()
        return self.lines
    
    def read_char(self): #read file charchater by charachter
        return self.file_in.read(1)

    def read_lines(self): #read file line by line
        return self.file_in.readlines()

    def write(self, txt): #writing to file
        for value in txt:
            print(value,end='',file=self.file_out)

    def close(self): #close all files
        self.file_in.close()
        self.file_out.close()



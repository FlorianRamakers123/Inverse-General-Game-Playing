import common
import subprocess
import prolog
import string
import config as cfg
import sys
sys.path.insert(1, '../utils')

from gamelib import *

def writefile(path, content):
        output_file = open(path, "w+") #create file is it doesn't exists
        output_file.write(content)
        output_file.close()

def readfile1(path):
    gfile = open(path, "r+") 
    return gfile.read()

def convertToMetagol(content):
    result = []
    lines = content.split("\n")
    for i in range(len(lines)):
        if lines[i] != "":
            t = convert_clause_to_metagol( lines[i].replace(".", "")) #no . needed beause convert method adds its own .
            result.append(t)

        

    t = "\n".join(result)
    t = t.replace("my_not_", "not_my_")
    t = unground_not(t)
    return t

    # convert a given prolog head to a head that corresponds to the metagol syntax
#ex. true(q) becomes true(A,q)
#ex. goal(robot, 100) becomes goal(A,robot, 100)
def convert_to_metagol_head(head):
    if "(" in head:
        return head.replace("(", "(A,", 1)
    else:
        return head + "(A)"

def convert_to_metagol_body_dot(body):
    return convert_to_metagol_body(body, ".")

def convert_to_metagol_body_comma(body):
    return convert_to_metagol_body(body, ",")

# convert a given prolog body to a body that corresponds to the metagol syntax
def convert_to_metagol_body(body, delimeter):
        if body.endswith("."):
            body=body[:-1]

        body_parts = []
        parenth_level = 0
        current_string = ""
        for i in range(len(body)):
            current_char = body[i]
            if current_char == '(':
                parenth_level += 1
                if (i < 2 or body[i-3:i] != "not"): # not used?
                    current_char += "A,"
            elif current_char == ')':
                parenth_level -= 1
            elif current_char == ',' and parenth_level == 0:
                body_parts.append(current_string)
                current_string = ""
                continue
            current_string += current_char
            if i == len(body) - 1:
                body_parts.append(current_string)

        #bij does mag er geen "my_" voor komen (wel een A bij argumenten)
        body_parts = [  ("my_" if not ("does" in x) else "") + x.strip() for x in body_parts]
        return  (delimeter + " ").join(body_parts)	+ "."	


def convert_clause_to_metagol(clause):
   # clause = unground_not(clause) #uit utils gamelib
    head = convert_to_metagol_head(clause.split(":-")[0].strip())

    if len(clause.split(":-")) == 2:
        body = (clause.split(":-")[1].strip())
        body2 = convert_to_metagol_body_comma(body)
        return head + ":- " + body2
    else:
        return head + "."

"""
def moveMYintoNOT(body_part):
    body_parts = []
    parenth_level = 0
    current_string = ""
    for i in range(len(body)):
        current_char = body[i]
        if current_char == '(':
            parenth_level += 1
            if (i < 2 or body[i-3:i] != "not"):
                current_char += "A,"
        elif current_char == ')':
            parenth_level -= 1
        elif current_char == ',' and parenth_level == 0:
            body_parts.append(current_string)
            current_string = ""
            continue
        current_string += current_char
        if i == len(body) - 1:
            body_parts.append(current_string)
"""

class Claudien:
    name='claudien'
    metagol_runner='metagol/runner'

    def __init__(self):
        pass

   

    def parse_test(self,datafile,outpath,game,target):
        for (subtarget,bk,pos,neg) in common.parse_target(datafile):
            #print("parsing (test) for claudien,", game, subtarget)
            common.parse_test(outpath,subtarget,bk,pos,neg)
    """
    def train(self,inpath,outfile,target):
        trainf=inpath+target
        prolog.swipl(action='learn,halt.',load_files=[self.metagol_runner,trainf],outfile=outfile,timeout=cfg.learning_timeout)
    """
    #programf is de geleerde hypothese file
    def do_test(self,dataf,programf,outf):
        #print( dataf)
        #print(programf)
        #print(outf)

        filename = programf.split("/")[-1]
        ##print(filename)
        if "my" in filename:
            ##ex. fizzbuzz next_my_succes.pl
            ##print("remove my in ", filename)
            filename = filename.replace("my_","")
            programf = "/".join(programf.split("/")[:-1]) + "/" + filename
           ## print("new programf", programf)

        #print(filename)
        newFilef = programf + "_met.pl"

        content = readfile1(programf)
        newContent = convertToMetagol(content)
        writefile(newFilef, newContent)

        prolog.swipl('do_test,halt.',[self.metagol_runner,dataf,newFilef],outf,timeout=None)



    
from pyswip import Prolog
from utils.tokenlib import tokenize_arguments,tokenize_prolog_body
import subprocess
import sys
def create_env():
    return Prolog()

def load_file(prolog,path):
    list(prolog.query("style_check(-singleton)"))
    list(prolog.query("style_check(-discontiguous)"))
    prolog.consult(path)

def unload_file(prolog,path):
    return bool(list(prolog.query("unload_file(\"{}\")".format(path))))

def findall2(prolog,pred):
    head_and_body = pred.split(":-")
    head_vars = get_variables(head_and_body[0])
    arg_str = ""
    if len(head_vars) > 0:
        arg_str = "[" + ", ".join(head_vars) + "]"
    else:
        body_vars = []
        for element in tokenize_prolog_body(pred):
            body_vars += get_variables(element)
        if len(body_vars) > 0:
            arg_str = "[" + ", ".join(body_vars) + "]"
        else:
            if query(prolog,head_and_body[0]):
                return {0}
            else:
                return set()
    query = "findall({},{},L)".format(arg_str,pred)
    return set([tuple(x) for x in list(prolog.query(query))[0]['L']])

def findall1(prolog,pred):
    head_and_body = pred.split(":-")
    n = len(tokenize_arguments(head_and_body[0]))
    if n < 0:
        body_vars = 0
        for element in tokenize_prolog_body(pred):
            body_vars += len(tokenize_arguments(head_and_body[0]))
        if body_vars > 0:
            n = body_vars
        elif query(prolog,head_and_body[0]):
            return {0}

    arg_str = "[" + ",".join([chr(ord('A') + i) for i in range(n)]) + "]"
    query = "findall({},{},L)".format(arg_str,pred)
    print(query)
    return set([str(tuple(x)) for x in list(prolog.query(query))[0]['L']])

def findall(file,call):
    p = create_env()
    a = list(p.query("style_check(-discontiguous)")) # moet om een of andere reden echt geitereerd worden
    a = list(p.query("style_check(-singleton)")) # moet om een of andere reden echt geitereerd worden
    p.consult(file)
    result = list(p.query(call))
    unload_file(p,file)
    return list(map(dict, set(tuple(sorted(d.items())) for d in result)))

def findall3(path,pred,call):
    # retrieve the head of the predicate
    head = pred.split(".\n")[0].split(":-")[0].strip()
    # check if the predicate has variables
    args = []
    #print(pred.strip())
    if '(' in head:
        args = tokenize_arguments(call)
    n = len(args)
    arg_str = "-".join(args)
    if n == 0:
        preds = pred.split(".\n")
        preds = list(filter(None,preds))
        #print(preds)
        instances = set()
        inst = -1
        for pred_clause in preds:
            ##### werkt niet voor ilasp
            #body_vars = set()
            #for element in tokenize_prolog_body(pred_clause):
            #    body_vars = body_vars.union(get_variables(element))
            #if len(body_vars) > 0:
            #    append_args = '(' ','.join(body_vars) + ')'
            #    instances = instances.union(perform_find_all('-'.join(body_vars),call+append_args,path))
            if True: #else:
                if pred_clause.split(":-")[1].strip() == "false":
                    continue
                while inst in instances:
                    inst += inst - 1
                instances.add(inst)

        return instances
    return perform_find_all(arg_str,call,path)

def perform_find_all(arg_str,call,path):
    fquery = "findall({},{},L).".format(arg_str,call)
    #print(fquery)
    (output,error) = swipl(fquery,[path])
    output = output.replace("\n","")
    list_content = output[output.find("L = ") + 5:-2]
    if list_content == "":
        return set()
    L = list_content.split(",")
    return set([tuple(x.strip().split("-")) for x in L])

def perform_find_all1(arg_str,call,path):
    fquery = "findall({},{},L).".format(arg_str,call)
    p = create_env()
    a = list(p.query("style_check(-discontiguous)")) # moet om een of andere reden echt geitereerd worden
    a = list(p.query("style_check(-singleton)")) # moet om een of andere reden echt geitereerd worden
    p.consult(path)
    result = list(p.query(fquery))
    unload_file(p,path)
    return result


def query(prolog,pred):
    return bool(list(prolog.query(pred)))

def perform_query(query,file):
    p = create_env()
    a = list(p.query("style_check(-discontiguous)")) # moet om een of andere reden echt geitereerd worden
    a = list(p.query("style_check(-singleton)")) # moet om een of andere reden echt geitereerd worden
    p.consult(file)
    result = bool(list(p.query(query)))
    unload_file(p,file)
    return result

def get_variables(fact):
    args = tokenize_arguments(fact.strip())
    return {arg for arg in args if arg[0].isupper()}

def swipl(action, load_files, suppress_warnings=True, timeout=None):
    prolog_version = 'swipl'
    cmd=""
    load_files = map(lambda x: "'{}'".format(x),load_files)
    if suppress_warnings:
        cmd +="style_check(-singleton), "
    cmd += "set_prolog_flag(answer_write_options,[max_depth(0)]),load_files([{}],[silent(true)]). ".format(','.join(load_files))
    cmd+=action

    p = subprocess.Popen([prolog_version,'-q'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return call_p(p,cmd,timeout)


def call_p(p,cmd,timeout):
    try:
        # print(cmd)
        p.stdin.write(cmd.encode())
        out, err = p.communicate(timeout=timeout)

        return (out.decode('utf-8'), err.decode('utf-8'))
    except Exception as e:
        print(e)
    finally:
        p.kill()

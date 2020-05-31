##### LIBRARY FOR WORKING WITH GDL FILES #####

# --------- TOKENIZATION OF GDL --------- #
# convert the contents of a GDL file to a list of facts and rules with prolog style variables
# @param gdl: the contents of a GDL file
def tokenize(gdl):
    # the list of tokens that will be filled
    tokens = []

    # the amount of closed parentheses we need to parse in order to have matched parentheses
    p_level = 0

    # the current token
    current_token = ""

    # boolean indicating whether we are in a comment
    in_comment = False

    # boolean indicating whether we ar in a variable
    in_variable = False

    # loop through each character of the GDL script
    for c in gdl:
        # ignore characters in comment until next line
        if in_comment:
            if c == '\n':
                in_comment = False
            else:
                continue

        # shift the first character of the variable to the upper variant
        if in_variable:
            c = c.upper()
            in_variable = False

        # start comment parsing
        if c == ';':
            in_comment = True
            continue
        # ignore new lines and tabs
        elif c in "\n\t":
            continue
        # ignore whitespaces if they are not used to seperate arguments and predicates
        elif c == ' ' and p_level == 0:
            continue
        # increase level of parentheses
        elif c == '(':
            p_level += 1
        # decrease level of parentheses
        elif c == ')':
            p_level -= 1
        # start variable parsing
        elif c == '?':
            in_variable = True
            continue

        # add the character to the current token
        current_token += c

        # if the parentheses match we have found a new token
        if p_level == 0:
            tokens.append(current_token)
            current_token = ""

    return tokens

# tokenize a gdl fact into the different parts
# @param gdl_fact: one fact from the gdl file
def tokenize_fact(gdl_fact):
    # the list of tokens that will be filled
    tokens = []

    # the amount of closed parentheses we need to parse in order to have matched parentheses
    p_level = 0

    # the current token
    current_token = ""

    # boolean indicating whether we ar in a variable
    in_variable = False

    # loop through each character of the rule
    for c in gdl_fact:
        # shift the first character of the variable to the upper variant
        if in_variable:
            c = c.upper()
            in_variable = False
        # ignore new lines and tabs
        elif c in "\n\t":
            continue
        # if we encounter a space than the current_token should be added, if not empty
        elif c == ' ' and p_level == 0:
            if current_token != "":
                tokens.append(current_token)
                current_token = ""
            continue
        # increase level of parentheses
        elif c == '(':

            if p_level == 0 and current_token != "":
                tokens.append(current_token)
                current_token = ""
            p_level += 1
        # decrease level of parentheses
        elif c == ')':
            p_level -= 1
        # start variable parsing
        elif c == '?':
            in_variable = True
            continue

        # add the character to the current token
        current_token += c

    if current_token != "":
        tokens.append(current_token)
    return tokens

# tokenize a gdl rule into the different parts
# @param gdl_rule: one rule from the gdl file
def tokenize_rule(gdl_rule):
    # delete the operator and tokenize it as a fact
    return tokenize_fact(gdl_rule.replace("<= ", "")[1:-1])

# --------- TOKENIZATION OF PROLOG --------- #

#ilasp produces hypotheses with 'not' 'space' instead of 'not' '('
def fix_not_ilasp(hyp):
    lines = hyp.split("\n")
    for j in range(len(lines)):
        if ":-" in lines[j]:
            parts = lines[j].split(":-")
            body = parts[1].strip()
            body_tokens = tokenize_prolog_body(body)
            for i in range(len(body_tokens)):
                if body_tokens[i].startswith("not "):
                    body_tokens[i] = body_tokens[i].replace("not ", "not(") + ")"
            lines[j] = parts[0].strip() + " :- " + ", ".join(body_tokens)
    return "\n".join(lines)


# returns the given string if it does not contain prolog, otherwise the empty string is returned
# @param gdl_line: one line from the GDL file
def remove_prolog(gdl_line):
    if ',' in gdl_line or ":-" in gdl_line or '.' in gdl_line or '%' in gdl_line:
        return ""
    else:
        return gdl_line

# tokenize the body of a prolog clause
# @param prolog_body: the body of the prolog body to tokenize
def tokenize_prolog_body(prolog_body):
    # the list of tokens that will be filled
    tokens = []

    # the amount of closed parentheses we need to parse in order to have matched parentheses
    p_level = 0

    # the current token
    current_token = ""

    # loop through each character of the body
    for c in prolog_body:
        # if we encounter a space than the current_token should be added, if not empty
        if c == ',' and p_level == 0:
            if current_token != "":
                tokens.append(current_token.strip())
                current_token = ""
            continue
        # increase level of parentheses
        elif c == '(':
            p_level += 1
        # decrease level of parentheses
        elif c == ')':
            p_level -= 1
        # delete spaces on level 0
        #elif c == ' ' and p_level == 0:
        #    continue
        # add the character to the current token
        current_token += c

    if current_token != "":
        tokens.append(current_token.strip())
    return tokens

# this variable must be set to the string "true" if the output predicates should be grounded
ground = "true"

# convert a gdl token to prolog
# @param gdl_token: one rule or fact from the gdl file
def construct_prolog_token(gdl_token):
    global ground
    if "<=" in gdl_token:
        if ground == "true":
            return ground_prolog_rule(construct_prolog_rule(gdl_token)) + "."
        else:
            return construct_prolog_rule(gdl_token)
    else:
        if ground == "true":
            return ground_prolog_fact(construct_prolog_fact(gdl_token)) + "."
        else:
            return construct_prolog_fact(gdl_token) + "."

# convert a gdl token to a prolog fact recursively
# @param: # @param gdl_token: one fact from the gdl file
def construct_prolog_fact(gdl_token):
    # remove outer parentheses
    # this also happens if there are no parentheses but this is not a problem
    gdl_base = gdl_token[1:-1]

    # get all tokens
    gdl_tokens = tokenize_fact(gdl_base)

    # if the result does not contain parentheses then we are in the base case
    if '(' not in gdl_base and ')' not in gdl_base:
        if len(gdl_tokens) > 1:
            return "{}({})".format(gdl_tokens[0], ", ".join(gdl_tokens[1:]))
        else:
            if gdl_token.startswith('('):
                return gdl_base + "()" # we need to do his because otherwise we wont recognize the difference between a constant and a predicat with arity = 0
            else:
                return gdl_token

    # convert to arguments to prolog
    gdl_prolog_args = map(construct_prolog_fact, gdl_tokens[1:])

    return "{}({})".format(gdl_tokens[0], ", ".join(gdl_prolog_args))

# convert a gdl token to a prolog rule
# @param gdl_token: one rule from the gdl file
def construct_prolog_rule(gdl_token):
    # get all the different elements of this rule
    rule_elements = tokenize_rule(gdl_token)
    if rule_elements[1:] == []:
        return "{} :- false.".format(construct_prolog_fact(rule_elements[0]))
    else:
        return "{} :- {}.".format(construct_prolog_fact(rule_elements[0]), ", ".join(map(construct_prolog_fact, rule_elements[1:])))

# ground the given prolog statement
# @param prolog: the prolog statement to ground
def ground_prolog(prolog):
    if ":-" in prolog:
        return ground_prolog_rule(prolog)
    else:
        return ground_prolog_fact(prolog)

# ground the given prolog fact
# @param prolog_fact: the prolog fact to ground
def ground_prolog_fact(prolog_fact):
    start_with_not = False
    # remove the end point
    if prolog_fact.endswith('.'):
        prolog_fact = prolog_fact[0:-1]
    # if it starts with not we need to remember this. If not, it will be grounded wrong
    if prolog_fact.startswith("not("):
        start_with_not = True
        prolog_fact = prolog_fact[4:-1]

    # count the parentheses
    par_count = prolog_fact.count('(')

    # if it does not contain any, then we have
    if par_count == 0:
        if start_with_not:
            return "not({})".format(prolog_fact)
        else:
            return prolog_fact

    # search the first parenthesis
    first_parenth = prolog_fact.find('(')

    # extract the predicate name
    pred_name = prolog_fact[0:first_parenth]

    # get the arguments
    # arguments can be variables or predicates
    pred_args = tokenize_prolog_body(prolog_fact[first_parenth + 1: -1])
    i = 0
    while i < len(pred_args):
        arg = pred_args[i]
        # we found a predicate with arity > 0
        if '(' in arg and not "()" in arg:
            first_parenth_arg = arg.find('(')
            pred_name_arg = arg[0:first_parenth_arg]
            pred_arg_args = tokenize_prolog_body(arg[first_parenth_arg + 1: -1])
            pred_args[i] = pred_arg_args[0]
            merge(pred_arg_args[1:], pred_args, i+1)
            pred_name += "_" + pred_name_arg
        # we found a predicate with arity = 0
        # WARNING: (next (gameOver) (gameOver2) x) will not be grounded correctly
        elif "()" in arg:
            pred_name += "_" + arg.replace("()", "")
            pred_args.remove(arg)
        i += 1

    if start_with_not:
        return "not({}({}))".format(pred_name,", ".join(pred_args))
    else:
        return "{}({})".format(pred_name,", ".join(pred_args))

def ground_not(prolog):
    if ':-' in prolog:
        rhs = prolog.split(':-')[0].strip()
        lhs = prolog.split(':-')[1].strip().replace(".","")
        new_lhs = []
        for body_elem in lhs.split(","):
            body_elem = body_elem.strip()
            if body_elem.startswith("not("):
                new_lhs.append(body_elem.replace("not(", "not_")[:-1])
            else:
                new_lhs.append(body_elem)
        return "{} :- {}".format(rhs, ",".join(new_lhs))
    else:
        if "not(" in prolog:
            return prolog.replace("not(", "not_").replace(".", "")[:-1]
        else:
            return prolog

# ground the given prolog rule
# @param prolog_rule: the prolog rule to ground
def ground_prolog_rule(prolog_rule):
    # split the head and the body
    head_and_body = prolog_rule.split(' :- ')
    # ground the head
    grounded_head = ground_prolog_fact(head_and_body[0])
    # ground the body
    grounded_body = ", ".join(list(map(ground_prolog_fact, tokenize_prolog_body(head_and_body[1]))))
    return grounded_head + " :- " + grounded_body

# put all elements of A in B starting at index i
# @param A: the list to insert
# @param B: the list to insert to
# @param i: the index to start from
def merge(A,B,i):
    # reverse A otherwise the elements will be inserted in the wrong order
    A.reverse()
    for a in A:
        B.insert(i,a)
    # reverse A back because lists are mutable and we don't want to change the original list
    A.reverse()
    return B

# delete starting and trailing whitespaces from the given string
# this function is defined to be used with map
# @param s: the string to strip
def strip(s):
    return s.strip()

# legalize the prolog in such a way that it doesn't redefine built-in predicates
# @param prolog: the prolog code to legalize
#TODO succ?
def legalize_prolog(prolog):
    builtins = ["number","close"]
    # readlines keeps the '\n' at the end so we must exclude the last character
    for builtin in builtins:
        prolog = prolog.replace(builtin + "(", "my" + builtin + "(")

    return prolog

# returns the arguments of this clause as a list
# @param clause: the clause to retrieve the arguments from
def tokenize_arguments(clause):
    if not "(" in clause:
        return [clause]
    if clause.endswith("."):
        clause = clause[0:-1]
    parent_index = clause.find("(")
    args = []
    args_str = clause[parent_index+1:-1]
    parent_lvl = 0
    curr_arg = ""
    for c in args_str:
        if c == '(':
            parent_lvl += 1
        elif c == ')':
            parent_lvl -= 1
        elif c == ',':
            args.append(curr_arg.strip())
            curr_arg = ""
            continue

        curr_arg += c

    if curr_arg != "":
        args.append(curr_arg)
    return args


def sort_ilasp_body(ilasp_body):
    tokens = tokenize_prolog_body(ilasp_body.strip())
    new_tokens = []
    for token in tokens:
        if '=' in token:
            new_tokens.insert(0,token)
        else:
            new_tokens.append(token)
    return ", ".join(new_tokens)


# --------- SORTING TOKENS --------- #

# the maximum length of a prolog rule
# this number can be arbitrary high, just for sorting purposes
MAX_PROLOG_RULE_LENGTH = 10000

# sort the tokens in such a way that the background information comes first
# @param tokens: the tokens to sort
def token_sort(tokens):
    # convert all tokens to key value pairs
    tuple_items = list(map(create_tuple, tokens))

    # sort the tuples based on the key
    tuple_items.sort(key=get_key)

    # return all the values of the tuples
    return map(get_value, tuple_items)

# create a key value pair that helps with sorting
# @param token: the token that will be converted to a key value pair
def create_tuple(token):
    if token.startswith("%%%%"):
        return (MAX_PROLOG_RULE_LENGTH, token)
    elif token.startswith("goal"):
        return (MAX_PROLOG_RULE_LENGTH + 1, token)
    elif token.startswith("legal"):
        return (MAX_PROLOG_RULE_LENGTH + 2, token)
    elif token.startswith("next"):
        return (MAX_PROLOG_RULE_LENGTH + 3, token)
    elif token.startswith("terminal"):
        return (MAX_PROLOG_RULE_LENGTH + 4, token)
    else:
        return (len(token), token)

# get the key the given key value pair
# @param tuple_item: the key value pair to retrieve the key from
def get_key(tuple_item):
    return tuple_item[0]

# get the value the given key value pair
# @param tuple_item: the key value pair to retrieve the value from
def get_value(tuple_item):
    return tuple_item[1]

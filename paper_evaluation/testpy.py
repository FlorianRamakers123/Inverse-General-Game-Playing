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
                if i < 2 or body[i-3:i] != "not":
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

        body_parts = ["my_" + x.strip() for x in body_parts]
        return  (delimeter + " ").join(body_parts)	+ "."	


def convert_clause_to_metagol(clause):
    head = convert_to_metagol_head(clause.split(":-")[0].strip())
    body = convert_to_metagol_body_comma(clause.split(":-")[1].strip())

    return head + ":- " + body

a = "legal(B, C):- input(B, C), mama(7)."

print(convert_clause_to_metagol(a))

from __future__ import print_function
from problog.formula import LogicFormula
from problog.engine import instantiate, UnifyError
from .engine import unify
from logging import getLogger as get_logger
import traceback
class Clause(object):
    """Represents a clause. 
    
    This in abstract class; see EmptyClause and ExtendedClause for implementations.

    A clause is the basic representation of what is to be learned.
    It is defined as a set of literals.

    A clause is represented as a linked list of ExtendedClauses starting with an EmptyClause.

    """
    
    def __init__(self, literal, refinements=None, blacklist=None):
        self.literal = literal
        self._next_refinements = refinements
        self._update_refinements()
        # Evaluation statistics
        self.successes = None
        self.failings = None
        self.verifications = None
        self.improvement = None
        self.blacklist = blacklist

    def _update_refinements(self):
        raise NotImplementedError()

    @property
    def literals(self):
        """Return a list of all literals in the clause.

        :return:
        :rtype: list[problog.logic.Term]
        """
        raise NotImplementedError()
 
    def __repr__(self):
        try:
            return ' \/ '.join(map(str, self.literals))
        except:
            return "clause"
    
    def get_body_literals(self):
        return [x for x in list(map(abs, self.literals_body)) if x.functor != '#']

    def __str__(self):
        head_lits = [x for x in self.literals_head if x.functor != '#']
        body_lits = [x for x in list(map(abs, self.literals_body)) if x.functor != '#']
        if body_lits and head_lits:
            return '%s -> %s' % (' /\\ '.join(map(str, body_lits)),
                                 ' \\/ '.join(map(str, head_lits)))
        elif body_lits:
            return '%s -> false' % (' /\\ '.join(map(str, body_lits)))
        elif head_lits:
            return '%s' % (' \\/ '.join(map(str, head_lits)))
        else:
            return 'false'
        
    def __add__(self, literal):
        return ExtendedClause(self, literal)
            
    @property
    def literals_head(self):
        """Return a list of all positive literals in the clause.

        :return: list[problog.logic.Term]
        """
        return [lit for lit in self.literals if not lit.is_negated()]
    
    @property
    def literals_body(self):
        """Return a list of all negative literals in the clause.

        :return: list[problog.logic.Term]
        """
        return [lit for lit in self.literals if lit.is_negated()]
        
    def __contains__(self, lit):
        return lit in self.literals
            
    def __len__(self):
        return len(self.literals)
        
    @classmethod
    def from_list(cls, lst):
        """Create a Clause from a list of literals.

        :param lst: list of literals in the clause
        :type lst: list[problog.logic.Term]
        :return: list of literals
        :rtype: Clause
        """
        res = EmptyClause()
        for lit in lst:
            res += lit
        return res

    @classmethod
    def literals_from_logic(cls, rule):
        from problog.logic import AnnotatedDisjunction, And
        from problog.logic import Clause as ClauseP

        if isinstance(rule, AnnotatedDisjunction):
            heads = rule.heads
            body = rule.body
        elif isinstance(rule, ClauseP):
            if rule.head.functor == '_directive':
                heads = []
            else:
                heads = [rule.head]
            body = rule.body
        else:
            heads = [rule]
            body = None

        body_list = []
        while isinstance(body, And):
            body_list.append(body.op1)
            body = body.op2
        if body is not None:
            body_list.append(body)

        return [-lit for lit in body_list] + [lit for lit in heads]

    @classmethod
    def from_logic(cls, rule):
        """Create a Clause from a parsed ProbLog rule.

        :param rule: ProbLog rule representing a clause
        :type rule: problog.logic.Term
        :return:
        :rtype: Clause
        """
        lits = cls.literals_from_logic(rule)

        variables = None
        for lit in lits:
            if variables is None:
                variables = lit.variables()
            else:
                variables |= lit.variables()
        subst = {v: i for i, v in enumerate(variables)}
        
        for lit in lits:
            lit.apply(subst)
        
        lits = [lit.apply(subst) for lit in lits]
        return Clause.from_list(lits)

    @property
    def introduces_variables(self):
        """Indicate whether the last literal added to the clause introduces new variables.

        :return: True if the last added literal introduces a new variable
        :rtype: bool
        """
        raise NotImplementedError()

    @property
    def language(self):
        """Return the language specification according to which this rule was generated.

        :return: Language
        """
        raise NotImplementedError()

    @language.setter
    def language(self, value):
        raise NotImplementedError()

    def evaluate(self, examples, engine):
        """Evaluate the given rule on the given examples in the given engine.

        :param examples: examples on which to evaluate this clause
        :type examples: data.Interpretations
        :param engine: the evaluation engine to use
        :type engine: problog.engine.Engine
        :return: True if the rule is valid on all examples, False otherwise
        :rtype: bool
        """
        raise NotImplementedError()

    def refine(self):
        raise NotImplementedError()

    def validate(self,examples,engine):
        raise NotImplementedError()

    def verify(self,examples,engine):
        raise NotImplementedError()

    def __lt__(self, other):
        try:
            return self.get_heuristic() > other.get_heuristic()
        except:
            #print("failed to find heuristic for ", self)
            return True

    def get_heuristic(self):
        pos_covered = len([failing for failing in self.failings if not failing])
        neg_not_covered = len([success for success in self.successes if success])
        return (pos_coverd + neg_nog_covered) / 2;


class EmptyClause(Clause):
    
    def __init__(self, language=None):
        self._language = language
        self.variable_count = 0
        self.variable_types = []
        self.variable_names = []
        self.root = self
        Clause.__init__(self, literal=None)

    @property
    def literals(self):
        return []

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, value):
        self._language = value

    def _update_refinements(self):
        if self.language:
            self._next_refinements = list(self.language.refine_initial(self))
            
    def refine(self):
        for ref in self.language.refine_initial(self):
            yield ref
        # for i, ref in enumerate(self._next_refinements):
        #     yield ExtendedClause(self, ref, refinements=self._next_refinements[i+1:])

    @property
    def introduces_variables(self):
        return False
        
    # evaluate this clause on the positive examples
    # a clause is valid if for every positive example, the body of the clause evaluates to false or the head of the clause is defined in the example
    # this class represents the "false" clause so it does not cover any example
    # therefore we add an element [[]] for every example
    def evaluate(self, examples, engine):
        self.failings = [[[]]] * len(examples)
        return False

    # validate this clause on the negative examples
    # a clause is valid if for every negative example, the body of the clause evaluates to false or the head of the clause is not defined in the example
    # this class represents the "false" clause so it covers every negative example
    # therefore we add an element [] for every example
    def validate(self,examples,engine):
        #print("validation (empty):",self)
        self.successes = [[[]]] * len(examples)
        return False

    def verify(self,examples,engine):
        self.verifications = [[[]]] * len(examples)
        return False

    def __lt__(self, other):
        return True

class ExtendedClause(Clause):
    """
    
    Note: 
        Variables with the same name in different literals will be translated to distinct variables
        To reuse variables you should use integers instead of Var objects.
    
    """
    
    def __init__(self, parent, literal, refinements=None):
        self.parent = parent
        self.root = self.parent.root
        self.variable_count = self.parent.variable_count
        
        # Find new variables => those with names
        replace = {}
        vartypes = []
        litvars = literal.variables()
        
        for var in litvars:
            from .refinement import TypedVar
            if isinstance(var, TypedVar):
                if type(var.name) == int:
                    while var.name >= self.variable_count:
                        vartypes.append(None)
                        self.variable_count += 1
                    if var.name >= self.parent.variable_count:
                        vartypes[var.name-self.parent.variable_count] = var.type
                    replace[var] = var.name
                else:
                    if var.name not in replace:
                        vartypes.append(var.type)
                        replace[var.name] = self.variable_count
                        self.variable_count += 1
            elif type(var) == int:
                replace[var] = var
                self.variable_count = max(self.variable_count-1, var) + 1
            else:
                raise ValueError("Not a valid variable value '%s'!" % var)
        
        literal = literal.apply(replace)
        if vartypes:
            self.variable_types = parent.variable_types + vartypes
        else:
            self.variable_types = parent.variable_types
            #print(self.variable_types)
        Clause.__init__(self, literal, refinements)
        
    @property
    def language(self):
        return self.root.language

    @language.setter
    def language(self, value):
        self.root.language = value
        self._init_refinements()
        
    @property
    def literals(self):
        return self.parent.literals + [self.literal]
        
    def _get_new_variables(self):
        return list(range(self.parent.variable_count, self.variable_count))

    def _init_refinements(self):
        self._next_refinements = list(self.language.refine(self))
            # [ref for ref in self.language.refine(self) if abs(ref).functor >= abs(self.literal).functor]

    def _update_refinements(self):
        if self.language:
            new_variables = self._get_new_variables()    # list<int> : variable names
            assert(self._next_refinements is not None)
            update = list(self.language.refine(self, use_variables=new_variables))
            self._next_refinements += update
        
    def refine(self):
        for i, ref in enumerate(self._next_refinements):
            yield ExtendedClause(self, ref, refinements=self._next_refinements[i+1:])

    @property
    def introduces_variables(self):
        return self.variable_count > self.parent.variable_count

    # evaluate this clause on the positive examples
    # a clause is valid if for every positive example, the body of the clause evaluates to false or the head of the clause is defined in the example
    # if the parent of an hypothesis covers a positive example, so will the refinement of this hypothesis.
    # so we check if the parent is valid for this example, if it is we do not have to check whether the refinement is also valid
    def evaluate(self, examples, engine):
        # UITLEG subst
        # bij elke refinement wordt er 1 predicaat toegevoegd aan de body of head (in ons geval enkel aan de body, aangezien we enkel in de modes '\+' gebruiken)
        # het toegevoegde predicaat zit vervat in 'rule_literal'
        # elke failing bevat een aantal lijsten, subst is telkens een pointer naar een van deze lijsten
        # het i-de element van subst is telkens de waarde van parameter Ai
        # Bv example: p(a). p(b). q(a,b)
        # huidige hypothese: p(A1) -> false
        #    ----> rule_literal is dus p(A1)!!
        # de originele failing zou dan zijn [[]] (zie evaluate van EmptyClause)
        # de nieuwe failing is nu [[a],[b]] aangezien er in het voorbeeld twee keer p(A1) voorkomt 
        # aangezien de body nu true en de head false (want die is altijd false in dit voorbeeld) dekt dit het voorbeeld niet
        # daarom staat er een 'if not head_literal and i == None' wat betekent dat als de rule_literal een body_literal is en als die true is in het voorbeeld
        # dan wordt het voorbeeld niet gedekt
        

        # gather the failings from the parent
        # the failings list contains for every example information about that example
        # if a failing element is just an empty list ([]) then the clause covers that example
        if self.parent.failings is not None:
            failings = self.parent.failings
        else:
            self.parent.evaluate(examples, engine)
            failings = self.parent.failings
         
        # check whether the literal is a body or a head literal
        # body literals are negated
        rule_literal = abs(self.literal)
        if not self.literal.is_negated():
            head_literal = True
        else:
            head_literal = False

        # boolean indicating whether there is an example which is not covered by this clause
        fails = False

        # the list that will contain the updated failings
        # later on self.failings will be set to this list
        new_failings = []

        # boolean indicating whether this clause is an improvement of its parent clause
        improvement = False
        if head_literal:
            improvement = True
        # loop through the examples and failings at the same time
        # 'example' contains the example and 'failing' contains information about coverage of the example by the parent
        for k,(example, failing) in enumerate(zip(examples, failings)):
            #print("-----------------------------------------------------")
            #print("testing",self,"on example",k+1)
            if failing:  # equivalent to if 'failing != []' so if this if succeeds, the parent does not cover the example
                
                # TODO: find out why this is necessary
                if hasattr(example, '_ground'):
                    formula = example._ground
                    formula.clear_queries()
                else:
                    formula = LogicFormula()                     # Load from cache
                # formula = LogicFormula()
                
                # construct a new list to store the failing information for this example
                # later on 'failing' will be replaced by 'new_failing'
                new_failing = []

                # calculate the contents of new_failing
                for subst in failing:
                    #print("rule_literal:",rule_literal)
                    #print("original subst:",subst)
                    # for every new variable this clause introduces, add a None element to the substances
                    if len(subst) < self.variable_count:
                        subst = subst + [None] * (self.variable_count - len(subst))
                        improvement = True  # adds a variable
                    #print("new subst:",subst)
                    # subst now contains a list where the ith element contains the value for the ith parameter of the rule_literal
                    # bv. instantiate(pred(A1,A2,A3),[a,b,None]) would result in pred(a,b,_)
                    literal = instantiate(rule_literal, subst)
                    #print("literal:",literal)

                    # formula contains a list queries   
                    # this list contains all the facts in the example of the literal
                    # bv example: pred1(a). pred1(b). pred2(b). pred3(a,b). 
                    #  literal = pred1(_)
                    #   queries: [pred1(a),pred1(b)]
                    formula = engine.ground(example.database, literal, target=formula, label='query')
                    #print("formula:",formula)
                    # q is the query
                    # if i == 0, the query is true
                    # if i == None, the query is false
                    # de uitbreiding van een clause dekt het positieve voorbeeld als rule_literal een body_literal is die naar false evalueert of
                    # of als rule_literal een head_literal is die naar true evalueert
                    for q, i in formula.queries():
                        # create a copy of the subst_new
                        subst_new = subst[:]
                        #print("q:",q)
                        try:
                            # try to unify the query with the rule literal and put the unifications in subst_new
                            unify(q, rule_literal, subst_new)
                            
                            #print("subst_new:",subst_new)
                            if len(set(subst_new)) == len(subst_new):
                                # TODO check subst_new is all different
                                # the head_literal evaluated to false
                                if head_literal and i is None:
                                    if None in subst_new:
                                        get_logger('claudette').error(' '.join(map(str, (list(example.database), self, failing, formula))))
                                        raise RuntimeError('This shouldn\'t happen!')
                                    #print("head query",q,"evaluated to false")
                                    new_failing.append(subst_new)
                                # the body literal evaluated in true
                                elif not head_literal and i == 0:
                                    new_failing.append(subst_new)
                                    #print("body query",q,"evaluated to true")
                        except UnifyError:
                            # if we have a unify error then the literal is not unifyable with the query
                            #print("unify error")
                            pass
                        #print("==========")
                    
                example._ground = formula
                new_failings.append(new_failing)
                #print("failing:",failing)
                #print("new_failing:",new_failing)
                # we check whether new_failing contains any items
                # if it doesn't then we know that the refinement covers the example 
                if new_failing:
                    # if new_failing contains less items than failing than this clause covers it 'more' than the parent so there is an improvement
                    if len(new_failing) < len(failing) or self.variable_count == 0: # the last statement is needed for terminal (otherwise terminal gives no contribution)
                        improvement = True
                    fails = True
                else: # new_failing == [] thus this example is now covered
                    assert failing
                    improvement = True  # failing eliminated
            else:
                # the parent covers this example, so the refinement covers this to
                new_failings.append([])
        self.failings = new_failings
        self.improvement = improvement

        # if fails is set to True, then the clause didn't cover a positive example so it is not a valid one and needs to be refined
        return not fails


    def validate(self, examples, engine):
        if self.parent.successes is not None:
            successes = self.parent.successes
        else:
            self.parent.validate(examples, engine)
            successes = self.parent.successes
        
        rule_literal = abs(self.literal)
        if not self.literal.is_negated():
            head_literal = True
        else:
            head_literal = False

        succeeds = False
        new_successes = []
    
        # loop through the examples and successes at the same time
        for k,(example, success) in enumerate(zip(examples, successes)):
            #print("-----------------------------------------------------")
            #print("testing",self,"on example",k+1)
            if success:          
                if hasattr(example, '_ground'):
                    formula = example._ground
                    formula.clear_queries()
                else:
                    formula = LogicFormula()                    
               
                new_success = []

                for subst in success:
                    #print("rule_literal:",rule_literal)
                    #print("original subst:",subst)

                    if len(subst) < self.variable_count:
                        subst = subst + [None] * (self.variable_count - len(subst))
                    #print("new subst:",subst)

                    literal = instantiate(rule_literal, subst)
                    #print("literal:",literal)

                    formula = engine.ground(example.database, literal, target=formula, label='query')
                    #print("formula:",formula)

                    for q, i in formula.queries():
                        subst_new = subst[:]
                        #print("q:",q)
                        try:
                            unify(q, rule_literal, subst_new)
                            
                            #print("subst_new:",subst_new)

                            if head_literal and i == 0:
                                if None in subst_new:
                                    get_logger('claudette').error(' '.join(map(str, (list(example.database), self, failing, formula))))
                                    raise RuntimeError('This shouldn\'t happen!')
                                #print("head query",q,"evaluated to true")
                                new_success.append(subst_new)
                            # the body literal evaluated in true
                            elif not head_literal and i == 0:
                                new_success.append(subst_new)
                                #print("body query",q,"evaluated to true")
                        except UnifyError:
                            # if we have a unify error then the literal is not unifyable with the query
                            #print("unify error")
                            pass
                        #print("==========")
                    
                example._ground = formula
                if str(rule_literal)[0] == '#':
                    new_successes.append([[]])
                else:
                    new_successes.append(new_success)
                #print("success:",success)
                #print("new_success:",new_success)

                if new_success:
                    succeeds = True

            else:
                new_successes.append([])
        self.successes = new_successes


        return not succeeds

    # check if there is a positive examples that succeeds
    # if this method evaluates to false, we throw away this hypothesis
    def verify(self, examples, engine):
        if self.parent.verifications is not None:
            verifications = self.parent.verifications
        else:
            self.parent.verify(examples, engine)
            verifications = self.parent.verifications
        
        # check whether the literal is a body or a head literal
        # body literals are negated
        rule_literal = abs(self.literal)
        if not self.literal.is_negated():
            head_literal = True
        else:
            head_literal = False

        verifies = False
        new_verifications = []

        for k,(example, verification) in enumerate(zip(examples, verifications)):
            #print("-----------------------------------------------------")
            #print("testing",self,"on example",k+1)
            if verification:          
                if hasattr(example, '_ground'):
                    formula = example._ground
                    formula.clear_queries()
                else:
                    formula = LogicFormula()                    
               
                new_verification = []

                for subst in verification:
                    #print("rule_literal:",rule_literal)
                    #print("original subst:",subst)

                    if len(subst) < self.variable_count:
                        subst = subst + [None] * (self.variable_count - len(subst))
                    #print("new subst:",subst)

                    literal = instantiate(rule_literal, subst)
                    #print("literal:",literal)

                    formula = engine.ground(example.database, literal, target=formula, label='query')
                    #print("formula:",formula)

                    for q, i in formula.queries():
                        subst_new = subst[:]
                        #print("q:",q)
                        try:
                            unify(q, rule_literal, subst_new)
                            
                            #print("subst_new:",subst_new)
                            #if len(set(subst_new)) == len(subst_new):
                            if head_literal and i == 0:
                                if None in subst_new:
                                    get_logger('claudette').error(' '.join(map(str, (list(example.database), self, failing, formula))))
                                    raise RuntimeError('This shouldn\'t happen!')
                                #print("head query",q,"evaluated to true")
                                new_verification.append(subst_new)
                            # the body literal evaluated in true
                            elif not head_literal and i == 0:
                                new_verification.append(subst_new)
                                #print("body query",q,"evaluated to true")
                        except UnifyError:
                            # if we have a unify error then the literal is not unifyable with the query
                            #print("unify error")
                            pass
                        #print("==========")
                    
                example._ground = formula
                if str(rule_literal)[0] == '#':
                    new_verifications.append([[]])
                else:
                    new_verifications.append(new_verification)
                #print("verification:",verification)
                #print("new_verification:",new_verification)

                if new_verification:
                    verifies = True

            else:
                new_verifications.append([])
        self.verifications = new_verifications

        return verifies

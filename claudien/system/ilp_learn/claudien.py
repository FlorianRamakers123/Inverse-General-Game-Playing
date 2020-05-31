from __future__ import print_function

from problog.logic import Term
from problog.engine import DefaultEngine, UnifyError
from problog.util import OrderedSet
from problog.engine_builtin import StructSort
from .engine import unify

from .clause import Clause, EmptyClause
from .learn import LearningProblem
from .reader import load_data
from logging import getLogger as get_logger

from datetime import datetime
import os
import signal
module_path = os.path.dirname(os.path.abspath(__file__))


class Claudien(LearningProblem):
    def __init__(self, data, neg_data, language, engine, maxlength=0):
        LearningProblem.__init__(self)
        self.data = data
        self.neg_data = neg_data
        self.language = language
        self.candidates = []
        self.clauses_store = ClauseTrie()
        self.clauses = []  # For output: in-order
        self.engine = engine
        self.maxlength = maxlength

    def refine(self, clause):
        return list(clause.refine())

    def is_valid(self, clause):
        valid_pos = clause.evaluate(self.data,self.engine)
        valid_neg = clause.validate(self.neg_data, self.engine)
        if not valid_pos:
            #print("\t", clause, "is not valid on the pos examples")
            return False
        if valid_neg or len(self.neg_data) == 0:
            #print("\t", clause, "is valid on pos en neg examples")
            return True
        else:
            #print("\t", clause, "is valid on pos but not on neg examples")
            return False

    def prune_refine_verbose(self, clause):
        if not self.prune_refine(clause):
            return False
        else:
            return True

    def prune_refine(self, clause):
        if self._prune_maxlength(clause):
            get_logger('claudien').debug('\tPRUNING CLAUSE %s', clause)
            get_logger('claudien').debug('\t\tMAXLENGTH %s', clause)
            return False
        if self._prune_trivial_true(clause):
            get_logger('claudien').debug('\tPRUNING CLAUSE %s', clause)
            get_logger('claudien').debug('\t\tTRIVIAL TRUE %s', clause)
            return False
        if self._prune_trivial_redundant(clause):
            get_logger('claudien').debug('\tPRUNING CLAUSE %s', clause)
            get_logger('claudien').debug('\t\tTRIVIAL REDUNDANT %s', clause)
            return False
        if self._prune_blacklist(clause):
            get_logger('claudien').debug('\tPRUNING CLAUSE %s', clause)
            get_logger('claudien').debug('\t\tSUBSUMED BY CORE %s', clause)
            return False
        return self.prune_clause(clause)

    def prune_clause(self, clause):
        if not clause.verify(self.data,self.engine):
            return False
        if self.clauses_store.find_subclause(clause):
            get_logger('claudien').debug('\tPRUNING CLAUSE %s', clause)
            get_logger('claudien').debug('\t\tSUBSUMED BY LEARNED %s', clause)
            return False

        # if self._prune_implied_by_background(clause) : return False
        return True

    def _prune_blacklist(self, clause):
        import sys
        if clause.root.blacklist:
            #print (clause, clause.root.blacklist)
            for bclause in clause.root.blacklist:
                for context in subset(number_vars(bclause), ground_vars(clause), [None]*10):
                    # print ('SUBSET!', bclause, 'of', clause, file=sys.stderr)
                    return True
        return False

    def _prune_contrib(self, clause):
        if clause.introduces_variables:
            return False
        elif clause.improvement is not None:
            return not clause.improvement
        else:
            return False

    def _prune_trivial_true(self, clause):
        return -clause.literal in clause.parent

    def _prune_trivial_redundant(self, clause):
        return clause.literal in clause.parent

    def _prune_trivial_unbound(self, clause):
        return bool(clause.variables) and not bool(clause.literals_body)

    def _prune_maxlength(self, clause):
        return self.maxlength and len(clause) > self.maxlength

    # def _prune_implied_by_background(self, clause):
    #     # Make an example containing all body literals.
    #     # Query head literals.
    #     db = self.engine.prepare(self.data.background)
    #
    #     variables = {v.name: (Constant('x%s' % (i + 1))) for i, v in enumerate(clause.variables)}
    #
    #     for term in self.language.facts:
    #         db += Term(term.functor, *([None] * term.arity), p=Constant(0.01))
    #
    #     for lit in clause.literals_body:
    #         # db += abs(lit).apply(variables).withProbability(Constant(0.5))
    #         db += Term('evidence', abs(lit).apply(variables), Term('true'))
    #
    #     or_l = Or.fromList([lit.apply(variables) for lit in clause.literals_head])
    #
    #     db += Clause(Term('_implied'), or_l)
    #     db += Term('query', Term('_implied'))
    #
    #     gp = self.engine.ground_all(db)
    #     score = SDD.createFrom(gp).evaluate()['_implied']
    #     return score >= 1 - 1e-10

    def next(self, iteration=None):
        # Find a new test.
        new_clauses = []
        # Go through all clauses and update
        new_candidates = []
        num_candidates = 0
        self.candidates.sort()
        for i, candidate in enumerate(self.candidates):
            get_logger('claudien').log(9, 'REFINING CANDIDATE %s', candidate)
            if self.is_valid(candidate):
                if self.prune_clause(candidate):
                    new_clauses.append(candidate)
                    self.clauses_store.append(candidate)
                    self.clauses.append(candidate)
                    get_logger('claudien').info('NEW CLAUSE %s', candidate)
            elif not self._prune_contrib(candidate):
                refs = self.refine(candidate)
                cands = filter(self.prune_refine_verbose, refs)
                if get_logger('claudien').level < 10:
                    for cand in cands:
                        get_logger('claudien').log(9, '\tNEW CANDIDATE %s', cand)
                new_candidates += cands
                for c in cands:
                    num_candidates += 1
            else:
                get_logger('claudien').debug('\t\tNO CONTRIBUTION %s', candidate)
                pass
            msg = '--- ITERATION: %d --- PROCESSED: %d/%d --- NUM CANDIDATES: %d --- NUM CLAUSES: %d ---'
            get_logger('claudien').info(msg, iteration, i + 1, len(self.candidates), num_candidates, len(self.clauses))
        get_logger('claudien').info('====== COMPLETED ITERATION ======')
        self.candidates = new_candidates
        return new_clauses

    def next2(self, iteration=None):
        # Find a new test.
        new_clauses = []
        # Go through all clauses and update
        new_candidates = []
        num_candidates = 0
        self.candidates.sort()
        for i, candidate in enumerate(self.candidates):
            get_logger('claudien').log(9, 'REFINING CANDIDATE %s', candidate)
            refs = self.refine(candidate)
            print(refs)
            cands = filter(self.prune_refine_verbose, refs)
            for cand in cands:
                get_logger('claudien').log(9, '\tNEW CANDIDATE %s', cand)
                if self.is_valid(cand) and not self._prune_contrib(cand):
                    if self.prune_clause(cand):
                        new_clauses.append(cand)
                        self.clauses_store.append(cand)
                        self.clauses.append(cand)
                        get_logger('claudien').info('NEW CLAUSE %s', cand)
                else:
                    new_candidates.append(cand)
                    num_candidates += 1

            msg = '--- ITERATION: %d --- PROCESSED: %d/%d --- NUM CANDIDATES: %d --- NUM CLAUSES: %d ---'
            get_logger('claudien').info(msg, iteration, i + 1, len(self.candidates), num_candidates, len(self.clauses))
        get_logger('claudien').info('====== COMPLETED ITERATION ======')
        self.candidates = new_candidates
        return new_clauses


    def init(self):
        self.candidates = [EmptyClause(language=self.language)]

    def get_model(self):
        """Extract the model."""
        pass

    def update(self, clauses):
        # self.clauses += clauses
        if self.candidates:
            return [self]
        else:
            return []

class ClauseTrie(object):
    def __init__(self, terms=None):
        self.terms = terms
        self.children = {}
        self.is_terminal = False
        self.append = self.add
        self.size = 0

    def add(self, clause):
        self.size += 1
        self._add(sorted(self._group_literals(self._number_vars(clause))))

    def _add(self, groups):
        current = self
        for key, terms in groups:
            try:
                group = current.children[key]
            except KeyError:
                group = {}
                current.children[key] = group
            try:
                current = group[terms]
            except KeyError:
                current = ClauseTrie(terms)
                group[terms] = current
        current.is_terminal = True

    def find_subclause(self, clause):
        context = [None] * 10
        result = self.find_subset(sorted(self._group_literals(self._ground_vars(clause))), context)
        # if not result :
        # print (self)
        #     print ('\n'.join(map(str,self)))
        #     print ('FIND SUBSET', clause)
        return result

    def find_subset(self, groups, context):
        if self.is_terminal:
            return True
        if groups:
            g = 0
            for ss_group, ss_terms in sorted(self.children.items()):
                while g < len(groups) and groups[g][0] < ss_group:
                    g += 1
                if g == len(groups):
                    return False
                if groups[g][0] == ss_group:
                    for terms, child in ss_terms.items():
                        for sub_context in self._subset(terms, groups[g][1], context):
                            if self._alldifferent(sub_context) and child.find_subset(groups[g + 1:], sub_context):
                                return True
            return False
        else:
            return False

    def __repr__(self):
        return '[CT: %s %s]' % (self.children, self.is_terminal)

    def __iter__(self):
        if self.is_terminal:
            yield ()
        for key, terms in self.children.items():
            for term, child in terms.items():
                for rest in child:
                    if key[0] == '-':
                        yield tuple([-t for t in term]) + rest
                    else:
                        yield term + rest

    def __len__(self):
        return self.size

    def _subset(self, terms_a, terms_b, context):
        """Verify whether termsA are a subset of termsB.

           :param terms_a: list of terms with numbered variables
           :param terms_b: list of terms with grounded variables
           :param context: list containing values (initially None) for each numbered variable that occurs in termsA
        """

        if not terms_a:
            yield context  # success!!
        else:
            term_a = terms_a[0]
            for term_b in terms_b:
                try:
                    new_context = context[:]
                    unify(term_b, term_a, new_context)
                    for new_context in self._subset(terms_a[1:], terms_b, new_context):
                        yield new_context
                except UnifyError:
                    pass

    def _replace_vars(self, clause, func):
        literals = sorted(clause.literals, key=StructSort)
        variables = OrderedSet()
        for lit in literals:
            variables |= lit.variables()

        subst = {v: func(i) for i, v in enumerate(variables)}
        return [lit.apply(subst) for lit in literals]

    def _number_vars(self, clause):
        return self._replace_vars(clause, lambda x: x)

    def _ground_vars(self, clause):
        return self._replace_vars(clause, lambda x: Term('x_%s' % x))

    def _group_by(self, func, lst):
        current_list = []
        current_key = None
        for el in lst:
            key, elem = func(el)
            if key != current_key:
                if current_list:
                    yield current_key, tuple(current_list)
                    current_list = []
                current_key = key
            current_list.append(elem)
        if current_list:
            yield current_key, tuple(current_list)

    def _group_literals(self, terms):
        def group_key(term):
            if term.is_negated():
                return '-' + (-term).signature, abs(term)
            else:
                return '+' + term.signature, abs(term)

        return list(self._group_by(group_key, terms))

    def _alldifferent(self, lst):
        lst_n = filter(lambda x: x is not None, lst)
        return len(set(lst_n)) == len(lst_n)


def subset(terms_a, terms_b, context):
    """Verify whether termsA are a subset of termsB.

       :param terms_a: list of terms with numbered variables
       :param terms_b: list of terms with grounded variables
       :param context: list containing values (initially None) for each numbered variable that occurs in termsA
    """

    if not terms_a:
        yield context  # success!!
    else:
        term_a = terms_a[0]
        for term_b in terms_b:
            try:
                new_context = context[:]
                unify(term_b, term_a, new_context)
                for new_context in subset(terms_a[1:], terms_b, new_context):
                    yield new_context
            except UnifyError:
                pass


def replace_vars(clause, func):
    literals = sorted(clause.literals, key=StructSort)
    variables = OrderedSet()
    for lit in literals:
        variables |= lit.variables()

    subst = {v: func(i) for i, v in enumerate(variables)}
    return [lit.apply(subst) for lit in literals]


def number_vars(clause):
    return replace_vars(clause, lambda x: x)


def ground_vars(clause):
    return replace_vars(clause, lambda x: Term('x_%s' % x))

def time1():
    return datetime.now().strftime("%H:%M:%S")

learn = None
tfilename = None
def run_claudien(filename, maxlength=0, **other):
    global learn, tfilename
    tfilename = filename
    language, instances, neg_data, engine = load_data(filename)
    learn = Claudien(instances, neg_data, language, engine, maxlength=maxlength)

    #signal.signal(signal.SIGINT, signal.default_int_handler) # redirect sigint to keyboardinterrupt
    signal.signal(signal.SIGINT, sigint_handler)
    try:
        #print("    claudien:", time1(), "--starting ", filename)
        print("    claudien:", time1(), "--starting ")
        learn.solve()
        #print("    claudien:", time1(), "--FINISHED ", filename)
        print("    claudien:", time1(), "--FINISHED ")
    except KeyboardInterrupt:
        pass
        print("--keyboard : timed-out")

    print("    claudien: after learn_solve()")
    r= ""
    for c in learn.clauses:
        print(c)
        r += str(c) + "\n"
    write_output(r, filename)


def sigint_handler(signal_received, frame):
    # Handle any cleanup here
   #print('SIGINT or CTRL-C detected. Exiting gracefully')
    print("--keyboard : timed-out")
    #print("    claudien: after learn_solve()")
    r= ""
    for c in learn.clauses:
        print(c)
        r += str(c) + "\n"
    write_output(r, tfilename)

def write_output(content, title):
    parts = title.split("/")
    file_parts = parts[-1].split("_")
    #print(parts[-1])
    pred = parts[-1].replace(parts[-4], "").replace("_train.dat", "").replace("_cwa.dat", "")[1:]
    #print(pred)
    filename =  module_path + "/../../output/" + parts[-4] + "/" + parts[-4] + "_" + pred + ".pl"
    #filename = filename.replace(".", "_out.")
    print("####", time1(), "going to write to:", filename)
    output_file = open(filename, "w") #create file is it doesn't exists # + weggelaten
    output_file.write(content)
    output_file.close()


def run_eval(filename, **other):
    from .data import read_data, concat, Interpretations, Instance
    from problog.program import PrologString
    # from problog.logic import AnnotatedDisjunction, Clause
    print("starting eval")
    data = read_data(filename)

    rules = concat(data['RULES'])

    engine = DefaultEngine()
    engine.prepare(PrologString(':- unknown(fail).'))

    background_pl = concat(data.get('BACKGROUND', []))

    examples = data.get('', [])
    examples_db = [engine.prepare(PrologString(background_pl + example_pl)) for example_pl in examples]
    instances = Interpretations([Instance(example_db) for example_db in examples_db], PrologString(background_pl))

    for rule in PrologString(rules):
        clause = Clause.from_logic(rule)
        print('Evaluation of rule:', clause)
        if not clause.evaluate(instances, engine):
            print('\tRule fails for: ')
            for ex, fail in enumerate(clause.failings):
                if fail:
                    print('\t\tExample %s:' % (ex + 1), fail)

        else:
            print('\tRule is valid.')


def run_eval_neg(filename, **other):
    from .data import read_data, concat, Interpretations, Instance
    from problog.program import PrologString
    # from problog.logic import AnnotatedDisjunction, Clause
    print("starting eval")
    data = read_data(filename)

    rules = concat(data['RULES'])

    engine = DefaultEngine()
    engine.prepare(PrologString(':- unknown(fail).'))

    background_pl = concat(data.get('BACKGROUND', []))

    examples = data.get('!', [])
    examples_db = [engine.prepare(PrologString(background_pl + example_pl)) for example_pl in examples]
    instances = Interpretations([Instance(example_db) for example_db in examples_db], PrologString(background_pl))

    for rule in PrologString(rules):
        clause = Clause.from_logic(rule)
        print('Evaluation of rule:', clause)
        if not clause.validate(instances, engine):
            print('\tRule is invalid')
            #for ex, success in enumerate(clause.successes):
            #    if not success:
            #        print('\t\tExample %s:' % (ex + 1), success)

        else:
            print('\tRule is valid.')

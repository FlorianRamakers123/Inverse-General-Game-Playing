from __future__ import print_function

from problog.logic import Var, Term, is_variable
from problog.program import PrologString
from problog.engine import DefaultEngine
from .clause import Clause
from logging import getLogger as get_logger


class RefinementOperator(object):
    
    def __init__(self):
        pass
    
    def refine_initial(self, rule):
        """Add the first literal to a rule.

        :param rule:
        :return:
        """
        raise NotImplementedError()
        
    def refine(self, rule, use_variables=None):
        """Generate all possible extensions of the given rule.

        :param rule:
        :param use_variables: the new literal should use one of these variables
        :return:
        """
        raise NotImplementedError()


class CModeLanguage(RefinementOperator):
    """A language based on modes.

    This language uses mode restrictions to restrict the generation process.

    Modes are specified in the following way:

    Core modes:
        Core modes define the initial form of a rule.
        Such a mode consists of a rule fragment.

        e.g.
            grandmother(A,B).                   % This should exist in the head.
            :- parent(A,B), parent(B,C).        % This should exist in the body.
            grandmother(A,B) :- parent(A,C).    % Both head and body are partially defined.

        These modes are only used at the very start of the rule generation process.

    Regular modes:
        The regular modes restrict how literals get added after the startup.

        Refinements to the head can be defined as:

           parent(+,+)

        In the head only modes + and c are allowed (to enforce range-restrictedness).

        Refinements to the body take negated literals:

            \+parent(+,-)

        In the body, modes +, - and c are allowed.
    """

    @classmethod
    def mode_is_use(cls, m):
        return str(m) == '+' or str(m) == "'+'"

    @classmethod
    def mode_is_add(cls, m):
        return str(m) == '-' or str(m) == "'-'"

    @classmethod
    def mode_is_constant(cls, m):
        return str(m) == 'c' or str(m) == "'c'"

    def __init__(self, cores, modes, types, constants, background):
        super(CModeLanguage, self).__init__()
        self.cores = cores
        self.modes = modes
        self.types = types
        self.constants = constants
        self.background = background

        for core in self.cores:
            core.language = self

    def refine_initial(self, rule):
        for c, core in enumerate(self.cores):
            core.root.blacklist = self.cores[:c]
            yield core

    def refine(self, rule, use_variables=None):
        for pos_neg, mode in self.modes:
            # Check whether we have a reuse mode.
            has_use = False
            for a in mode.args:
                if self.mode_is_use(a):
                    has_use = True
                    break
            # If we don't reuse variables, then we can ignore use_variables.
            if not has_use:
                use_variables = None
            # Get the variable types.
            argtypes = self.types[mode.signature]
            # Generate a refinement.
            for args in self._refine(rule, mode.args, argtypes, use_variables):
                res = mode(*args)
                if not pos_neg:
                    res = -res
                yield res

    def _refine(self, rule, argmodes, argtypes, use_variables, newvars=0):
        if not argmodes and not argtypes:
            # We reached the end of the argument list.
            if use_variables is None:
                # There are no variables that have to be used.
                yield ()
        else:
            # Generate all possibilities for the first argument, and recurse for the next arguments.
            for arg, use_variables1, newvars1 in self._refine_single(rule, argmodes[0], argtypes[0], use_variables, newvars):
                for args in self._refine(rule, argmodes[1:], argtypes[1:], use_variables1, newvars1):
                    yield (arg,) + args

    def _refine_single(self, rule, argmode, argtype, use_variables, newvars=0):
        if self.mode_is_add(argmode):
            # Create a new variable
            yield TypedVar('V%s' % newvars, argtype), use_variables, newvars + 1
        elif self.mode_is_use(argmode):
            # Pick an existing variable from the rule
            for c in range(0, rule.variable_count):
                #print(str(rule.variable_types))
                if rule.variable_types[c] == argtype:
                    # The variable has the right type.
                    if use_variables is not None and c in use_variables:
                        yield c, None, newvars
                    else:
                        yield c, use_variables, newvars
        else:
            # Pick a constant
            for c in self.constants[argtype]:
                yield c, use_variables, newvars

    @classmethod
    def load(cls, filedata):
        engine = DefaultEngine()

        cores_l = []
        cores = []
        modes = []
        types = {}
        constants = {}
        constant_modes = []
        
        # Load the cores.
        cores_str = '\n'.join(filedata.get('CORES', []))
        for core in PrologString(cores_str):
            core_literals = Clause.literals_from_logic(core)
            cores_l.append(core_literals)

        # Load the modes.
        modes_str = '\n'.join(filedata.get('MODES', []))
        for mode_term in PrologString(modes_str):
            if mode_term.is_negated():
                mode_term = -mode_term
                modes.append((False, mode_term))
            else:
                modes.append((True, mode_term))
            for i, a in enumerate(mode_term.args):
                if cls.mode_is_constant(a):
                    constant_modes.append((mode_term.signature, i))

        # Load the types.
        all_types = set()
        types_str = '\n'.join(filedata.get('TYPES', []))
        for type_term in PrologString(types_str):
            predicate = type_term.signature
            argtypes = type_term.args
            for argtype in argtypes:
                all_types.add(argtype)
            types[predicate] = argtypes

        # Load the constants.
        constants_str = '\n'.join(filedata.get('CONSTANTS', []))
        constants_db = engine.prepare(PrologString(constants_str))
        for t in all_types:
            values = [x[0] for x in engine.query(constants_db, t(None))]
            if values:
                constants[t] = values

        # Change variables in cores
        for core_l in cores_l:
            core = []
            varreplace = {}
            vars_head = set()
            vars_body = set()
            new_vars = 0
            for lit in core_l:
                if lit.is_negated():
                    negated = True
                    lit = -lit
                else:
                    negated = False
                new_args = []
                for arg_i, arg_v in enumerate(lit.args):
                    if isinstance(arg_v, Var) or is_variable(arg_v):
                        if arg_v in varreplace:
                            new_var = varreplace[arg_v]
                            new_args.append(new_var)
                        else:
                            if lit.signature not in types:
                                raise InvalidLanguage('No type specified for predicate \'%s\'.' % lit.signature)
                            argtype = types[lit.signature][arg_i]
                            new_var = TypedVar(new_vars, argtype)
                            new_vars += 1
                            varreplace[arg_v] = new_var
                            new_args.append(new_var)
                        if negated:
                            vars_body.add(new_var)
                        else:
                            vars_head.add(new_var)
                    else:
                        new_args.append(arg_v)
                new_lit = lit(*new_args)
                if negated:
                    new_lit = -new_lit
                core.append(new_lit)
            for var in vars_head - vars_body:
                core.insert(0, -Term('#', var.type, var))
                # raise InvalidLanguage('Core rule is not range-restricted.')
            cores.append(Clause.from_list(core))

        from problog.logic import Clause as ClauseP
        background = []
        for pred, args in types.items():
            pred = pred.rsplit('/', 1)[0]
            for i, a in enumerate(args):
                argl = [None] * len(args)
                argl[i] = 0
                background.append(ClauseP(Term('#', a, 0), Term(pred, *argl)))

        # Verify the extracted information:
        #  - we need at least one core
        if not cores:
            raise InvalidLanguage('At least one core is required.')
        #  - we need at least one mode
        if not modes:
            raise InvalidLanguage('At least one mode is required.')
        #  - only + and c allowed in positive modes
        for pn, mode in modes:
            if pn:
                for arg in mode.args:
                    if cls.mode_is_add(arg):
                        raise InvalidLanguage('New variables are not allowed in head of clause: \'%s\'.' % mode)
        #  - we need types for all modes
        missing_types = []
        for _, mode in modes:
            if mode.signature not in types:
                missing_types.append(mode.signature)
        if missing_types:
            raise InvalidLanguage('Types are missing for %s.' % and_join(missing_types))

        #  - when a 'c' mode is used, we need constants for that type
        missing_constants = set()
        for cs, ci in constant_modes:
            argtype = types[cs][ci]
            if argtype not in constants:
                missing_constants.add(argtype)
        if missing_constants:
            raise InvalidLanguage('Constants are missing for type %s.' % and_join(missing_constants))

        return CModeLanguage(cores, modes, types, constants, background)


def and_join(lst):
    lst = list(lst)
    if len(lst) == 1:
        return lst[0]
    else:
        return ' and '.join([', '.join(lst[:-1]), lst[-1]])


class InvalidLanguage(Exception):

    def __init__(self, *args):
        super(InvalidLanguage, self).__init__(*args)


# class AModeLanguage(RefinementOperator):
#
#     def __init__(self, modes, types, constants):
#         RefinementOperator.__init__(self)
#         self.modes = modes
#         self.types = types
#         self.constants = constants
#
#     def __repr__(self):
#         return 'AModeLanguage: %s %s %s' % (self.modes, self.types, self.constants)
#
#     def _refine_initial_single(self, arg_mode, arg_type, types=None):
#         if types is None:
#             types = []
#         if self.mode_is_add(arg_mode):
#                     return
#         elif self.mode_is_use(arg_mode):
#             if not types:
#                 yield TypedVar(0, arg_type), [arg_type]
#             else:
#                 # TODO check types
#                 for c, t in enumerate(types):
#                     if t == arg_type:
#                         yield TypedVar(c, arg_type), types
#                 yield TypedVar(len(types), arg_type), types + [arg_type]
#         else:
#             for c in self.constants[arg_type]:
#                 yield c, types
#
#     def _refine_initial(self, arg_modes, arg_types, types=None):
#         if types is None:
#             types = []
#         if arg_modes and arg_types:
#             for arg, types_new in self._refine_initial_single(arg_modes[0], arg_types[0], types):
#                 for args in self._refine_initial(arg_modes[1:], arg_types[1:], types_new):
#                     yield (arg,) + args
#         else:
#             yield ()
#
#     def refine_initial(self, rule):
#         for mode in self.modes:
#             arg_types = self.types[(mode.functor, mode.arity)]
#             for args in self._refine_initial(mode.args, arg_types):
#                 yield -mode(*args)
#             if mode.arity == 0:
#                 yield mode
#
#     def _refine_single(self, rule, arg_mode, arg_type, use_variables, n=0, positive=False):
#         if self.mode_is_add(arg_mode):
#             if not positive:
#                 yield TypedVar('V%s' % n, arg_type), use_variables, n+1
#         elif self.mode_is_use(arg_mode):
#             for c in range(0, rule.variable_count):
#                 if rule.variable_types[c] == arg_type:
#                     if use_variables is not None and c in use_variables:
#                         yield c, None, n
#                     else:
#                         yield c, use_variables, n
#         else:
#             for c in self.constants[arg_type]:
#                 yield c, use_variables, n
#
#     def _refine(self, rule, arg_modes, arg_types, use_variables, m=0, positive=False):
#         if arg_modes and arg_types:
#             for arg, uv, m2 in self._refine_single(rule, arg_modes[0], arg_types[0], use_variables, m, positive):
#                 for args in self._refine(rule, arg_modes[1:], arg_types[1:], uv, m2, positive):
#                     yield (arg,) + args
#         elif use_variables is None:
#             yield ()
#
#     def refine(self, rule, use_variables=None):
#         for mode in self.modes:
#             all_new = True
#             for a in mode.args:
#                 if not self.mode_is_add(a):
#                     all_new = False
#             if all_new:
#                 use_variables1 = None
#             else:
#                 use_variables1 = use_variables
#             arg_types = self.types[(mode.functor, mode.arity)]
#             for args in self._refine(rule, mode.args, arg_types, use_variables1):
#                 if not self._is_up_list(args):
#                     yield -mode(*args)
#             if not all_new:
#                 for args in self._refine(rule, mode.args, arg_types, use_variables, positive=True):
#                     yield mode(*args)
#
#     @classmethod
#     def mode_is_use(cls, m):
#         return str(m) == '+' or str(m) == "'+'"
#
#     @classmethod
#     def mode_is_add(cls, m):
#         return str(m) == '-' or str(m) == "'-'"
#
#     @classmethod
#     def mode_is_constant(cls, m):
#         return str(m) == 'c' or str(m) == "'c'"
#
#     @classmethod
#     def _is_up_list(cls, l):
#         m = -1
#         for x in l:
#             if isinstance(x, Var):
#                 return False
#             elif not type(x) == int:
#                 pass
#             elif x <= m:
#                 pass
#             elif x == m+1:
#                 m = x
#             else:
#                 return False
#         return True
#
#     @classmethod
#     def load(cls, data):
#         engine = DefaultEngine()
#         background_pl = '\n'.join(data.get('BACKGROUND', []))
#
#         language_facts = list(PrologString('\n'.join(data['FACTS'])))
#         background = list(PrologString(background_pl))
#         language_db = engine.prepare(language_facts + background)
#
#         language_modes = list(PrologString('\n'.join(data['MODES'])))
#         mode_terms = set()
#         mode_constants = {}
#         for term in language_modes:
#             mode_terms.add((term.functor, term.arity))
#             positions = [i for i, c in enumerate(term.args) if str(c) in ("'c'", 'c')]
#             if positions:
#                 mode_constants[(term.functor, term.arity)] = positions
#
#         language_section = list(PrologString('\n'.join(data['TYPES'])))
#         language_types = list(language_section)
#         if language_types:
#             language_constants = defaultdict(set)
#         else:
#             constant_types = defaultdict(list)
#             language_types = []
#             for func, arit in mode_terms:
#                 types = engine.query(language_db, Term(func, *([None] * arit)))
#                 if (func, arit) in mode_constants:
#                     positions = mode_constants[(func, arit)]
#                 else:
#                     positions = []
#                 for tp in types:
#                     tp = list(map(str, tp))
#                     language_types.append(Term(func, *tp))
#                     for p in positions:
#                         constant_types[tp[p]].append((func, arit, p))
#
#             language_constants = defaultdict(set)
#             for tp, lst in constant_types.items():
#                 for func, arit, pos in lst:
#                     for inst in instances:
#                         for args in engine.query(inst.database, Term(func, *[None] * arit)):
#                             language_constants[tp].add(args[pos])
#
#         types = {}
#         for t in language_types:
#             types[(t.functor, t.arity)] = t.args
#
#         return AModeLanguage(language_modes, types, language_constants)


class TypedVar(Var):
    
    def __init__(self, name, vtype):
        Var.__init__(self, name)
        self.type = vtype
        
    def variables(self, **kwargs):
        return {self}


# def varlist(current, argtypes, vartypes, allow_new=True):
#     """
#     Generate argument lists for a predicate in canonical order.
#     :param current: Current argument list of predicate.
#     :type current: ( tuple of (int|Constant) | None )
#     :param argtypes: Types of arguments. If argument is a Constant, should be list of Constants.
#     :type argtypes: list of (Constant | list of Constant )
#     :param vartypes: dict of (int, Constant)
#     :param allow_new: allow new variables
#     :type: bool
#     :return: Sequence of possible argument lists, strictly larger than the current.
#     :rtype: generator of ( tuple of (int|Constant) | None )
#     """
#
#     length = len(argtypes)
#     maxvar = len(vartypes)
#
#     if length == 0:
#         yield ()
#     elif type(argtypes[0]) == list or type(argtypes[0]) == tuple:
#         # It's a constant
#         if current is not None:
#             s = argtypes[0].index(current[0]) + 1
#             if length > 1:
#                 for vs in varlist(current[1:], argtypes[1:], vartypes, allow_new):
#                     yield (current[0],) + vs
#         else:
#             s = 0
#         for i in range(s, len(argtypes[0])):
#             v = argtypes[0][i]
#             for vs in varlist(None, argtypes[1:], vartypes, allow_new):
#                 yield (v,) + vs
#     else:
#         if current is not None:
#             s = current[0]+1
#             if length > 1:
#                 for vs in varlist(current[1:], argtypes[1:], vartypes, allow_new):
#                     yield (current[0],) + vs
#         else:
#             s = 0
#         for v in range(s, maxvar+1):
#             if v >= maxvar:  # This is a new variable.
#                 if allow_new:
#                     for vs in varlist(None, argtypes[1:], vartypes + [argtypes[0]], allow_new):
#                         yield (TypedVar(v, argtypes[0]),) + vs
#             elif argtypes[0] == vartypes[v]:
#                 for vs in varlist(None, argtypes[1:], vartypes, allow_new):
#                     yield (v,) + vs

#
# def refine(clause, predicates):
#     """
#     Generate all refinements of the given clause.
#     :param clause: Current clause.
#     :type clause: Clause
#     :param predicates: List of literals with argument types.
#     :type predicates: list of Term
#     :return:
#     """
#
#     predicate_index = {t.signature: i for i, t in enumerate(predicates)}
#
#     current_literal = clause.literal
#     if current_literal is None:
#         # This is an initial clause.
#         current_predicate = -1
#         current_arguments = None
#         variable_types = []
#         is_negative = True
#     else:
#         assert isinstance(clause, ExtendedClause)
#         is_negative = current_literal.is_negative()
#         current_literal = abs(current_literal)
#         current_predicate = predicate_index[current_literal.signature]
#         current_arguments = current_literal.args
#         variable_types = clause.variable_types
#
#     if is_negative:
#         if current_predicate >= 0:
#             for arglist in varlist(current_arguments, predicates[current_predicate].args, variable_types,
#                                    allow_new=True):
#                 yield -current_literal(*arglist)
#
#         for predicate in predicates[current_predicate+1:]:
#             for arglist in varlist(None, predicate.args, variable_types, allow_new=True):
#                 yield -predicate(*arglist)
#
#         current_predicate = -1
#         current_arguments = None
#
#     if current_predicate >= 0:
#         for arglist in varlist(current_arguments, predicates[current_predicate].args, variable_types, allow_new=False):
#             yield current_literal(*arglist)
#
#     for predicate in predicates[current_predicate+1:]:
#         for arglist in varlist(None, predicate.args, variable_types, allow_new=False):
#             yield predicate(*arglist)


# class OptimalLanguage(RefinementOperator):
#
#     def __init__(self, predicates):
#         RefinementOperator.__init__(self)
#         self.predicates = predicates
#
#     def refine_initial(self, rule):
#         return self.refine(rule)
#
#     def refine(self, rule, use_variables=None):
#         return refine(rule, self.predicates)


def run_enum(filename, maxlength=3, **other):
    from .reader import load_data
    from .claudette import EmptyClause
    language, instances, engine = load_data(filename)

    rule = EmptyClause(language)
    rules = list(rule.refine())
    count = 0
    get_logger('claudette').log(9,'%% ---- Length 1 ----')
    for rule in rules:
        print (rule)
        count += 1
    level = 1 
    maxlength = 3
    while (maxlength is None or level < maxlength) and rules:
        new_rules = []
        print ('%% ---- Length %s ----' % (level + 1))
        for rule in rules:
            for rule1 in rule.refine():
                new_rules.append(rule1)
                print(str(rule1))
                count += 1
        rules = new_rules
        level += 1
    print ('Number of rules:', count)


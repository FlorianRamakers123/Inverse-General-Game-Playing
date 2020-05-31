from __future__ import print_function

from problog.sdd_formula import SDD
from problog.logic import Term, Var
from collections import defaultdict


def read_data(filename):
    sections = defaultdict(list)

    section_name = 'PREAMBLE'
    section = ''
    with open(filename) as f:
        for line in f:
            if line.lstrip('%\t ').startswith('==='):
                if section:
                    sections[section_name].append(section)
                section = ''
                section_name = line.strip('%\t =\n\r')
            else:
                section += line
        if section:
            sections[section_name].append(section)
    return sections


def concat(lists):
    if lists:
        res = lists[0]
        for s in lists[1:]:
            res += s
        return res
    else:
        return ''


class KnowledgeBase(object):

    def __init__(self):
        pass

    def evaluate(self, rule, engine, **kwargs):
        pass

    def __len__(self):
        pass


class EvaluationResult(object):
    """Result of evaluating a hypothesis on all examples."""

    def __init__(self, index, result):
        self.index = index
        self.score = result[Term('score')]
        self.failing = []
        if not self:
            for k, v in result.items():
                if k.functor == 'failing' and k.arity > 0:
                    ks = k.args
                    ks = {str(vn): vv for vn, vv in zip(ks[:len(ks) / 2], ks[-len(ks) / 2:])}
                    self.failing.append((ks, v))
                elif k.functor == 'failing':
                    self.failing.append(({}, v))

    def __nonzero__(self):
        return self.score > 1 - 1e-8

    def __float__(self):
        return self.score

    def __str__(self):
        return '%s : %s' % (self.score, self.failing)


class GlobalEvaluationResult(object):

    def __init__(self, results, skipped=set()):
        self.skipped = skipped
        self.success = set()
        self.failure = set()
        self.details = {}

        self.total_score = 0.0
        for index, result in results:
            self.total_score += float(result)
            if result:
                self.success.add(index)
            else:
                self.failure.add(index)
                self.details[index] = result


class DefDict(dict):

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return Var(key)


class Instance(object):

    def __init__(self, example):
        self.database = example
        # for clause in example :
        #     self.database += clause

    def evaluate_incremental(self, rule, engine, index=None):
        if rule.parent is not None:
            inst = self
            fail = rule.parent._eval.details[index]
            for subst, score in fail.failing:
                subst2 = DefDict()
                subst2.update(subst)
                lit_eval = engine.query(inst.database, rule.literal.apply(subst2))
                print(rule, rule.literal, subst, lit_eval)
        else:
            return self.evaluate_base(rule, engine, index)

    def evaluate_base(self, rule, engine, index=None):
        query_database = self.database.extend()
        for clause in rule.asLP(with_substitutions=True):
            query_database += clause
        gp = engine.ground_all(query_database)
        result = SDD.createFrom(gp).evaluate()
        return EvaluationResult(index, result)

    def evaluate(self, rule, engine, index=None):
        # Add clause:
        # self.evaluate_incremental(rule,engine,index)
        return self.evaluate_base(rule, engine, index)


class Interpretations(KnowledgeBase):

    def __init__(self, instances, background):
        super(Interpretations, self).__init__()
        self.background = background
        self.instances = instances

    def __getitem__(self, key):
        return self.instances[key]

    def __len__(self):
        return len(self.instances)

    def __iter__(self):
        return iter(self.instances)

    def evaluate(self, rule, engine, subset=None):
        if subset is not None:
            return GlobalEvaluationResult([(index, self[index].evaluate(rule, engine, index)) for index in subset],
                                          subset)
        else:
            return GlobalEvaluationResult(
                [(index, instance.evaluate(rule, engine, index)) for index, instance in enumerate(self.instances)])

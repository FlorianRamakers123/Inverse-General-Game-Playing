from problog.engine import DefaultEngine
from problog.logic import Constant, Term
from problog.engine_unify import unify_call_head


def unify(a, b, context):
    return unify_call_head([a], [b], context)


class SkolemEngine(DefaultEngine):
    
    def handle_nonground(self, context=None, target=None, **kwdargs):
        if not hasattr(target, 'skolem'):
            target.skolem = 0
        new_result = []
        for r in context:
            if r is None:
                new_result.append(Term('skolem', Constant(target.skolem)))
                target.skolem += 1
            else:
                new_result.append(r)
        return tuple(new_result)


if __name__ == '__main__':
    
    import sys
    import problog
    
    filename = sys.argv[1]
    
    pl = problog.program.PrologFile(filename)
    eng = SkolemEngine()
    
    gp = eng.ground_all(pl)
    
    sdd = problog.sdd_formula.SDD.createFrom(gp)
    
    print (sdd.evaluate())

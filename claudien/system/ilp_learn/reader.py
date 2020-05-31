from problog.program import PrologString
from problog.engine import DefaultEngine

from .data import Interpretations, Instance, read_data
from .refinement import CModeLanguage


def load_data(filename, engine=None):
    if engine is None:
        engine = DefaultEngine()
        engine.prepare(PrologString(':- unknown(fail).'))

    data = read_data(filename)

    background_pl = list(PrologString('\n'.join(data.get('BACKGROUND', []))))

    language = CModeLanguage.load(data)

    background_pl += language.background

    examples = data.get('', [])
    examples_db = [engine.prepare(background_pl + list(PrologString(example_pl))) for example_pl in examples]
    instances = Interpretations([Instance(example_db) for example_db in examples_db], background_pl)

    neg_examples = data.get('!', [])
    #print("the negative examples are {}".format("".join(neg_examples)))
    neg_examples_db = [engine.prepare(background_pl + list(PrologString(neg_example_pl))) for neg_example_pl in neg_examples]
    neg_instances = Interpretations([Instance(neg_example_db) for neg_example_db in neg_examples_db], background_pl)

    return language, instances, neg_instances, engine

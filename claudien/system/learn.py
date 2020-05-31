#! /usr/bin/env python

from ilp_learn.claudien import run_claudien, run_eval, run_eval_neg
from ilp_learn.refinement import run_enum
import sys
import logging


def init_logger(verbose=None, name='claudien', out=None):
    """Initialize default logger.

    :param verbose: verbosity level (0: WARNING, 1: INFO, 2: DEBUG)
    :type verbose: int
    :param name: name of the logger (default: problog)
    :type name: str
    :param out: output stream to write to
    :return: result of ``logging.getLogger(name)``
    :rtype: logging.Logger
    """
    if out is None:
        out = sys.stdout
    
    logger = logging.getLogger(name)
    ch = logging.StreamHandler(out)
    logger.addHandler(ch)

    if not verbose:
        logger.setLevel(logging.WARNING)
    elif verbose == 1:
        logger.setLevel(logging.INFO)
    elif verbose == 2:
        logger.setLevel(logging.DEBUG)
    else:
        level = max(1, 12 - verbose)   # between 9 and 1
        logger.setLevel(level)
    return logger


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    
    parser_eval = subparsers.add_parser('eval')
    parser_eval.add_argument('filename')
    parser_eval.set_defaults(func=run_eval)

    parser_validate = subparsers.add_parser('validate')
    parser_validate.add_argument('filename')
    parser_validate.set_defaults(func=run_eval_neg)
    
    parser_learn = subparsers.add_parser('claudien')
    parser_learn.add_argument('filename')
    parser_learn.add_argument('--maxlength', '-L', type=int)
    parser_learn.set_defaults(func=run_claudien)
    
    parser_enum = subparsers.add_parser('enum')
    parser_enum.add_argument('filename')
    parser_enum.add_argument('--maxlength', '-L', type=int)
    parser_enum.set_defaults(func=run_enum)

    parser_eval.add_argument('-v', '--verbose', action='count', help='verbosity level', default=0)
    parser_learn.add_argument('-v', '--verbose', action='count', help='verbosity level', default=0)
    parser_enum.add_argument('-v', '--verbose', action='count', help='verbosity level', default=0)
    parser_validate.add_argument('-v', '--verbose', action='count', help='verbosity level', default=0)

    #init_logger(9, name='claudien', out=None)
    #run_eval_neg("../test_neg.pl")
    args = parser.parse_args()

    #filename = "./claudien_output/out.txt"
   # out_stream = open(filename, "w+") # = None
    
    init_logger(args.verbose, name='claudien', out=None)

    args.func(**vars(args))

"""

This script was created to minimize and analyze finite automata (FA).
The FA provided as input should be a well-specified.
Running this sript without parameter will verify correctness of the FA
 and will output the automata in normalised form.
Parameters: 
 --help                     Outputs the help message.
 --input=<filename>         The input will be read from the <filename>.
 --output=<filename>        The output will be saved to <filename>.
 -f (--find-non-finishing)  The output is the only non-finishing state.
 -m (--minimize)            The output is minimal FA
 -i (--case-insensitive)    The character size will not be taken into
                            account while comparing the symbols or the states.

If the -m or -f flag is not stated, the script will only perform validation
of the well-specified FA and its normalised output.

"""


import sys
import getopt
import re

import exit_codes
from finite_automata import FiniteAutomata
from finite_automata import WellSpecifiedFA
from finite_automata import FAException


def print_stderr(*args, **kwargs):
    """Behave the same way as print() but by default prints on stderr"""
    print(*args, file=sys.stderr, **kwargs)


def get_options():
    """To get options and values as a dictionary {'option': value}"""
    longopts = [
        'help', 'input=', 'output=', 
        'find-non-finishing', 'minimize', 'case-insensitive'
    ]
    opts_dict = {}
    try:
        options, args = getopt.getopt(sys.argv[1:], 'fim', longopts)
        if args: # args list is not empty
            raise getopt.GetoptError(
                'invalid program argument \'' + args[0] + '\'')
       
        opts_list = [opt[0] for opt in options]
        if len(opts_list) != len(set(opts_list)):
            raise getopt.GetoptError(
                'cannot combine two or more same options')

        if all(opt in opts_list for opt in ['--minimize', '-m']):
            raise getopt.GetoptError(
                    'cannot combine two or more same options')

        if (all(opt in opts_list 
            for opt in ['--find-non-finishing', '-f'])):
            raise getopt.GetoptError(
                    'cannot combine two or more same options')

        if all(opt in opts_list for opt in ['--case-insensitive', '-i']):
            raise getopt.GetoptError(
                    'cannot combine two or more same options')        

        if (('-m' in opts_list or '--minimize' in opts_list) and
            ('-f' in opts_list or '--find-non-finishing' in opts_list)):
            raise getopt.GetoptError('cannot combine \'minimize\' and '
                '\'find-non-finishing\' options')

        for arg in sys.argv[1:]:
            arg_input_output = (arg[2:].startswith('output') or
                arg[2:].startswith('input'))

            if arg_input_output and re.match(r'\w+=.+', arg[2:]) is None:
                raise getopt.GetoptError(
                    'option \'' + arg + '\' requires argument')
    except getopt.GetoptError as opt_error:
        print_stderr(sys.argv[0], ': ', end='', sep='')
        print_stderr(opt_error)
        sys.exit(exit_codes.ERR_ARGS)

    for opt in options:
        opt_str = opt[0][2:]
        if re.match(r'^\-[^\-]', opt[0]):
            if opt[0] == '-m':
                opt_str = 'minimize'
            elif opt[0] == '-f':
                opt_str = 'find-non-finishing'
            else:
                opt_str = 'case-insensitive'

        opts_dict[opt_str] = opt[1]
            
    return opts_dict


if __name__ == '__main__':
    options = get_options()
    if 'help' in options:
        print(__doc__)
        sys.exit(exit_codes.SUCCESS)

    if 'input' in options:
        try:
            input_file = open(options['input'], encoding='utf-8')
            input_file_content = input_file.read()
            input_file.close()
        except IOError as io_error:
            io_error.strerror = 'cannot open file for reading'
            print_stderr(sys.argv[0], io_error.strerror,
                    sep=': ', end=' ')
            io_error.filename = '\'{}\''.format(io_error.filename)
            print_stderr(io_error.filename)
            sys.exit(exit_codes.ERR_INPUT)
    else:
        input_file_content = sys.stdin.read()

    if 'case-insensitive' in options:
        input_file_content = input_file_content.lower()
    try:
        fa = FiniteAutomata(input_file_content)
        well_specified_fa = WellSpecifiedFA(fa)
    except FAException as exc:
        print_stderr(exc)
        sys.exit(exc.code)

    if 'output' in options:
        try:
            output_file = open(options['output'], 
                    encoding='utf-8', mode='w')
        except IOError as io_error:
            io_error.strerror = 'cannot open file for writing'
            print_stderr(sys.argv[0], io_error.strerror,
                    sep=': ', end=' ')
            io_error.filename = '\'{}\''.format(io_error.filename)
            print_stderr(io_error.filename)
            sys.exit(exit_codes.ERR_INPUT)
    else:
        output_file = sys.stdout

    if 'find-non-finishing' in options:
        nonterm_s = well_specified_fa.get_nonterminating_states()
        if nonterm_s:
            print(nonterm_s.pop(), file=output_file, end='')
        else:
            print('0', file=output_file, end='')
            
        sys.exit(exit_codes.SUCCESS)

    well_specified_fa.minimize()
    print(well_specified_fa, file=output_file)
    output_file.close()
    sys.exit(exit_codes.SUCCESS)

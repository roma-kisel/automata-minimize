"""
This module was created to simplify work with finite automata

"""
import re
import itertools

import exit_codes


class FAException(Exception):
    """
    Represents the error that may occur when working with finite automata

    """
    _base_msg = 'fa file error: '

    def __init__(self, errmsg, code):
        self.errmsg = errmsg
        self.code = code

    def __str__(self):
        return FAException._base_msg + self.errmsg


class FASyntaxException(FAException):
    """Represents syntax exception"""
    def __init__(self, errmsg, code=exit_codes.ERR_SYNTAX):
        FAException.__init__(self, errmsg, code)
        FAException._base_msg += 'syntax error: '


class FASemanticException(FAException):
    """Represents semantic exception"""
    def __init__(self, errmsg, code=exit_codes.ERR_SEMANTIC):
        FAException.__init__(self, errmsg, code)
        FAException._base_msg += 'semantic error: '


_fsm_state_pattern = r'([a-zA-Z](?:[a-zA-Z_\d]*[a-zA-Z\d])?)'
_fsm_sym_pattern = r'(\'{2,4}|\'[^\']\')'
_fsm_component_pattern = r'\{(.*)\}'

_fsm_rule_pattern = _fsm_state_pattern + r'\s*' + _fsm_sym_pattern \
    + r'\s*->\s*' + _fsm_state_pattern

_fsm_pattern = r'^\s*\(\s*' + _fsm_component_pattern \
    + r'\s*,\s*' + _fsm_component_pattern \
    + r'\s*,\s*' + _fsm_component_pattern \
    + r'\s*,\s*' + _fsm_state_pattern \
    + r'\s*,\s*' + _fsm_component_pattern \
    + r'\s*\)\s*$'


def _check_get_states(states_content):
    if  re.match(r'^\s*$', states_content) is not None:
        return set()

    states_pattern = r'^(\s*' \
        + _fsm_state_pattern + r'\s*,)*\s*' \
        + _fsm_state_pattern + r'\s*$'

    if re.match(states_pattern, states_content) is None:

        raise FASyntaxException('bad states definition')

    states = set()
    for match in re.finditer(_fsm_state_pattern, states_content):
        states.add(match.group(0))

    return states


def _get_input_symbol(sym_content):
    if sym_content == '\'\'': # if sym is epsilon
        return ''
    elif sym_content == '\'\'\'':
        return None
    elif sym_content == '\'\'\'\'':
        return '\''
    else:
        return sym_content[1:-1]


def _check_get_alphabet(alphabet_content):
    alphabet_pattern = r'^(\s*' \
        + _fsm_sym_pattern + r'\s*,)*\s*' \
        + _fsm_sym_pattern + r'\s*$'

    if re.match(alphabet_pattern, alphabet_content, re.S) is None:
        raise FASyntaxException('bad alphabet definition')

    alphabet = set()
    for match in re.finditer(_fsm_sym_pattern, alphabet_content, re.S):
        input_symbol = _get_input_symbol(match.group(0))
        if input_symbol is None:
            raise FASyntaxException(
                'bad symbol \"{}\"'.format(match.group(0)))
        else:
            alphabet.add(input_symbol)

    return alphabet


def _check_get_rules(rules_content):
    rules_pattern = r'^(\s*' \
        + _fsm_rule_pattern + r'\s*,)*\s*' \
        + _fsm_rule_pattern + r'\s*$'

    if re.match(rules_pattern, rules_content, re.S) is None:
        raise FASyntaxException('bad rules definition')

    rules = set()
    for match in re.finditer(_fsm_rule_pattern, rules_content, re.S):
        state = match.group(1)
        input_symbol_content = match.group(2)
        input_symbol = _get_input_symbol(input_symbol_content)
        if input_symbol is None:
            raise FASyntaxException(
                'in rule \'{}\' bad symbol definition \"{}\"'
                    .format(match.group(0)), input_symbol_content)
        next_state = match.group(3)
        rules.add(Rule(state, input_symbol, next_state))

    return rules


class Rule:
    """Represents the rule"""
    def __init__(self, state, input_symbol, next_state):
        self.input_symbol = input_symbol
        self.state = state
        self.next_state = next_state

    def __eq__(self, other):
        return (self.input_symbol, self.state, self.next_state) \
            == (other.input_symbol, other.state, other.next_state)

    def __hash__(self):
        return hash((self.input_symbol, self.state, self.next_state))

    def __str__(self):
        return '{} \'{}\' -> {}'.format(
            self.state, self.input_symbol, self.next_state)


class FiniteAutomata:
    """Represents the finite automata"""
    def __init__(self, fa_file_content):
        fa_file_content = re.sub(
            r'(?<!\')#.*$', '', fa_file_content, flags=re.MULTILINE)

        match = re.match(_fsm_pattern, fa_file_content, re.S)
        
        if match is None:
            raise FASyntaxException('bad finite automata format')

        # print('states', match.group(1), sep=': ')
        self.states = _check_get_states(match.group(1))
        if not self.states:
            raise FASemanticException('states set should not be empty')

        self.alphabet = _check_get_alphabet(match.group(2))
        self.rules = _check_get_rules(match.group(3))

        if re.match(_fsm_state_pattern, match.group(4)) is None:
            raise FASyntaxException('bad start symbol definition')

        self.start_state = match.group(4)
        self.final_states = _check_get_states(match.group(5))
        self._check_semantic()

    def _check_semantic(self):
        if self.start_state not in self.states:
            raise FASemanticException(
                'unrecognized start state \'{}\''.format(self.start_state)
            )
        for rule in self.rules:
            if rule.input_symbol not in self.alphabet:
                raise FASemanticException(
                    'unrecognized input symbol \'{}\' in rule \'{}\''
                        .format(rule.input_symbol, rule)
                )
            elif rule.state not in self.states:
                raise FASemanticException(
                    'unrecognized state \'{}\' in rule \'{}\''
                        .format(rule.state, rule)
                )
            elif rule.next_state not in self.states:
                raise FASemanticException(
                    'unrecognized next state \'{}\' in rule \'{}\''
                        .format(rule.next_state, rule)
                )
            elif not self.final_states.issubset(self.states):
                raise FASemanticException(
                    'final states is not subset of states'
                )
            else:
                pass

    def deterministic(self):
        """Returns True if the finite automata is well specified. Else returns False"""
        for rule in self.rules:
            if rule.input_symbol == '':
                return False

        state_symbol_list = \
            [(rule.state, rule.input_symbol) for rule in self.rules]

        if len(state_symbol_list) != len(set(state_symbol_list)):
            return False

        return True
    
    def complete(self):
        """Returns True if the finite automata is complete. Else returns False"""
        for state in self.states:
            state_input_symbols = set([rule.input_symbol \
                    for rule in self.rules if rule.state == state])

            if self.alphabet != state_input_symbols:
                return False

        return True

    def all_states_are_accessible(self):
        """Returns True if all states are accessible. Else returns False"""
        next_states = set([rule.next_state for rule in self.rules])
        for state in self.states:
            if state != self.start_state and not state in next_states:
                return False

        return True

    def get_nonterminating_states(self):
        """Returns nonterminating_states in set form"""
        term = set(self.final_states)
        copy_rules = set(self.rules)
        while True:
            new_term = set()
            rules_to_del = set()    
            for rule in copy_rules:
                if rule.state not in term and rule.next_state in term:
                    new_term.add(rule.state)
                    rules_to_del.add(rule)
            copy_rules = copy_rules - rules_to_del
            if len(new_term) == 0:
                break
            term = term | new_term

        return self.states - term

    def __str__(self):
        ret_str = '(\n{'
        states_list = list(self.states)
        states_list.sort()
        for i, state in enumerate(states_list):
            if i + 1 == len(states_list):
                ret_str += state
            else:
                ret_str += '{}, '.format(state)
        ret_str += '},\n{'
        alphabet_list = list(self.alphabet)
        alphabet_list.sort()
        for i, input_symbol in enumerate(alphabet_list):
            if input_symbol == '\'':
                input_symbol = '\'\'' 

            if i + 1 == len(alphabet_list):
                ret_str += '\'{}\''.format(input_symbol)
            else:
                ret_str += '\'{}\', '.format(input_symbol)
        ret_str += '},\n{\n'
        rules_list = list(self.rules)
        rules_list.sort(key=lambda rule: (rule.state, rule.input_symbol))
        for i, rule in enumerate(rules_list):
            if i + 1 == len(rules_list):
                ret_str += '{}\n'.format(rule)
            else:
                ret_str += '{},\n'.format(rule)
        ret_str += '},\n'
        ret_str += '{},\n'.format(self.start_state)
        ret_str += '{'
        final_states_list = list(self.final_states)
        final_states_list.sort()
        for i, final_state in enumerate(final_states_list):
            if i + 1 == len(final_states_list):
                ret_str += final_state
            else:
                ret_str += '{}, '.format(final_state)
        ret_str += '}\n)'
        return ret_str


def _gen_subsets(some_set):
    for i in range(1, len(some_set)):
        for sub in [set(x) for x in itertools.combinations(some_set, i)]:
            yield (sub, some_set - sub)


def _connect_states(set_states):
    ret_state = ''
    list_states = list(set_states)
    list_states.sort()
    for i, state in enumerate(list_states):
        if i + 1 == len(list_states):
            ret_state += state
        else:
            ret_state += '{}_'.format(state)
    return ret_state


class WellSpecifiedFA(FiniteAutomata):
    """Represents well specified finite automata"""
    def __init__(self, fa):
        self.states = fa.states
        self.alphabet = fa.alphabet
        self.rules = fa.rules
        self.start_state = fa.start_state
        self.final_states = fa.final_states

        err_msg = 'not well specified: {}'
        if not fa.deterministic():
            err_msg = err_msg.format('not deterministic')
        elif not fa.complete():
            err_msg = err_msg.format('not complete')
        elif not fa.all_states_are_accessible():
            err_msg = err_msg.format('states are not accessible')
        elif len(fa.get_nonterminating_states()) > 1:
            err_msg = err_msg.format(
                'number of nonterminating states > 1')
        else:
            return

        raise FAException(err_msg, exit_codes.FA_NOT_WELL_SPEC) 

    def _get_rules_with_states_sym(self, states, symbol):
        ret_rules = set()
        for rule in self.rules:
            if rule.state in states and rule.input_symbol == symbol:
                ret_rules.add(rule)
        return ret_rules 

    def _get_next_states_rule_set(self, rule_set):
        next_states = set()
        for rule in rule_set:
            next_states.add(rule.next_state)
        return next_states

    def minimize(self):
        """Performs minimazing of the finite automata"""
        Qm = set()
        Qm.add(frozenset(self.final_states))
        Qm.add(frozenset(self.states - self.final_states))
        while True:
            was_division = False
            for symbol in self.alphabet:
                updated_Qm = set(Qm)
                for Q1 in Qm:
                    if len(Q1) == 1:
                        continue
                    rules_Q1_sym = \
                        self._get_rules_with_states_sym(Q1, symbol)
                    next_states = \
                        self._get_next_states_rule_set(rules_Q1_sym)
                    for q1_set, q2_set in _gen_subsets(next_states):
                        if q1_set.issubset(Q1) and not q2_set & Q1:
                            was_division = True
                            X1 = set()
                            for rule in rules_Q1_sym:
                                if rule.next_state in q2_set:
                                    X1.add(rule.state)
                            X2 = set()
                            for rule in rules_Q1_sym:
                                if rule.next_state in q1_set:
                                    X2.add(rule.state)

                            updated_Qm.remove(X1 | X2)
                            updated_Qm.add(frozenset(X1))
                            updated_Qm.add(frozenset(X2))
                            Qm = updated_Qm
            if not was_division:
                break
        Rm = set()
        for X in Qm:
            for Y in Qm:
                for x in X:
                    for y in Y:
                        for sym in self.alphabet:
                            if Rule(x, sym, y) in self.rules:
                                state = _connect_states(X)
                                next_state = _connect_states(Y)
                                Rm.add(Rule(state, sym, next_state))
        for q in Qm:
            if self.start_state in q:
                self.start_state = _connect_states(q) # set start state
                break
        Fm = set()
        for X in Qm:
            if X & self.final_states:
                Fm.add(X)

        self.states.clear()
        for Q in Qm:
            self.states.add(_connect_states(Q))
        self.rules.clear()
        for R in Rm:
            self.rules.add(R)
        self.final_states.clear()
        for F in Fm:
            self.final_states.add(_connect_states(F))

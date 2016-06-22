# TODO:
#   - handle nullables correctly
#   - handle right recursion correctly
#   - extract (via DFS?) a parse tree from the forest
#   - standardize and implement a tokenizer / parser for converting (E)BNF
#     grammars into objects the parser can deal with

from collections import deque
from orderedset import OrderedSet


def chart(grammar, start, inp):
    """ Construct an Earley parse chart for a stream of tokens `inp` given a
    grammar and a starting rule from the grammar.

    Inputs:
        grammar (dict-like): the grammar must support retrieving productions via
                             indexing by a nonterminal
        start (token): this is the key in the grammar from which to initialise
                       the chart
        inp (iterable of tokens)

    Returns:
        chart (list[set[tuple]]): each set in the list is a State Set
        corresponding by index to an input token; each tuple in each set is an
        Earley Item, corresponding to a partial parse.

    Note:
        The representation chosen for tokens (strings, objects, whatever) is
        wholly irrelevant to `chart` so long as it remains consistent across the
        grammar, the starting point, and the input stream.
    """
    # initialize
    history = []
    activeQ = deque()
    nextQ = deque([(start, rule, 0, 0) for rule in grammar[start]])

    # run
    for i, ch in enumerate(inp + [None]):
        history.append(OrderedSet())
        activeQ, nextQ = nextQ, activeQ

        while activeQ:
            item = activeQ.popleft()
            history[-1].add(item)

            key, rule, dot, index = item
            if dot < len(rule):
                if rule[dot] in grammar:
                    activeQ.extend(predictor(
                        rule[dot], grammar, history[i], i)
                    )
                else:
                    nextQ = scanner(item, ch, nextQ)
            else:
                activeQ.extend(completer(
                    key, history[index], history[i])
                )

    return history


def parse(chart, inp):
    search_chart = []
    #  search from end && filtr out non-complete items
    for page in reversed(chart):
        search_chart.append(OrderedSet(item
            for item in page if (item[2] >= len(item[1]))
        ))
    return search_chart


def recognizer(start, last_page):
    return any((index == 0 and key == start and dot >= len(rule))
               for item in last_page
               for key, rule, dot, index in item)


def predictor(key, grammar, seen, i):
    return [(key, production, 0, i)
            for production in grammar[key]
            if (key, production, 0, i) not in seen]


def completer(key, search_set, seen):
    return [(pk, pr, pd+1, pi)
            for pk, pr, pd, pi in search_set
            if (pd <= len(pr)
                and key == pr[pd]
                and (pk, pr, pd+1, pi) not in seen)
            ]


def scanner(item, token, Q):
    key, rule, dot, index = item
    scanned = (key, rule, dot+1, index)
    if rule[dot] == token and scanned not in Q:
        Q.append((key, rule, dot+1, index))
    return Q


def print_chart(chart, rev=False):
    def ruler(i):
        return '{} {} {}'.format('='*6, i, '='*50)
    def key(i,k):
        return '({:>2}) {:>12} -> '.format(i,k)
    def rule(item):
        out = ''
        for i, comp in enumerate(item[1]):
            if i == item[2]:
                out += ' @ '
            out += '{} '.format(comp)
        if item[2] >= i+1:
            out += ' @ '
        return out

    page_counter = range(len(chart)-1, -1, -1) if rev else range(len(chart))
    for i, page in zip(page_counter, chart):
        print(ruler(i))
        for j, item in enumerate(page):
            print('\t{:<20}{:<25}({})'.format(
                key(j, item[0]), rule(item), item[3]
            ))


def small_test():
    grammar = {
        'P': [('S',)],
        'S': [('S', '+', 'M'), ('M',)],
        'M': [('M', '*', 'T'), ('T',)],
        'T': [('1',), ('2',), ('3',), ('4',)]
    }

    test_case = '2+3*4'
    results = chart(grammar, 'P', list(test_case))
    print(recognizer('P', results))
#   print_chart(results)


def larger_test():
    grammar = {
        'START':    [('Sum',)],
        'Sum':      [('Product',),
                     ('Sum', '+', 'Product' ),
                     ('Sum', '-', 'Product' )],
        'Product':  [('Factor',),
                     ('Product', '*', 'Factor'),
                     ('Product', '/', 'Factor')],
        'Factor':   [('(', 'Sum', ')'), ('Number',)],
        'Number':   [('Digit', 'Number'), ('Digit',)],
        'Digit':    list(map(tuple, '0123456789')),
    }
    test_case = '1+(2*3-4)'
    results = chart(grammar, 'START', list(test_case))
    print(recognizer('START', results))
    print_chart(results)
#   print_chart(parse(results, list(test_case)))


if __name__ == "__main__":
#   small_test()
    larger_test()

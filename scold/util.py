"""
Utility module.
"""
try:
    from shlex import quote as shell_quote  # Python 3.3
except ImportError:
    from pipes import quote as shell_quote  # Python 2.x

import subprocess


def discrete_ranges(values, succ=lambda x: x + 1):
    """Cluster given values into a sequence of discrete ranges.

    :param values: Iterable of values
    :param succ: Successor function; default is 'increment by 1'

    :return: List of tuples describing ranges: [(begin, end)]
             where begin <= end, as per ``succ`` function
    """
    ranges = []
    last = None
    for x in sorted(values):
        if last is None:
            start = last = x
        else:
            if x == succ(last):
                last = x
            else:
                ranges.append((start, last))
                last = None
    if last is not None:
        ranges.append((start, last))

    return ranges


def shell(prog, *args, **kwargs):
    """Runs a shell command.

    Positional arguments are used as command arguments.
    Keyword arguments are used as flags.

    :return: Output of the command (stdout)
    """
    cmd_parts = [prog]
    cmd_parts.extend(map(shell_quote, args))
    for flag, value in kwargs.iteritems():
        prefix = '-' if len(flag) == 1 else '--'
        cmd_parts.append((prefix + flag.replace('_', '-')))
        if value and value is not True:
            cmd_parts.append(shell_quote(value))

    cmd = ' '.join(cmd_parts)
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out, _ = process.communicate()
    return out

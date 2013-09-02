"""
Sublime Scold

Streamlines telling off your coworkers for their lousy code.

:author: Karol Kuczmarski "Xion"
"""
from itertools import izip
from pipes import quote as shell_quote
import subprocess

from sublime_plugin import TextCommand


class Scold(TextCommand):

    def run(self, edit):
        # TODO: format & send mail to those poor folks
        print self._get_selection_authors()

    def _get_selection_authors(self):
        filename = self.view.file_name()
        sel = self.view.sel()
        if not (filename and sel):
            return ()

        line_numbers = self._get_line_numbers(self.view.sel())
        line_ranges = discrete_ranges(line_numbers)

        authors = set()
        for line_range in line_ranges:
            blamed_lines = git_blame(filename, lines=line_range)
            for line in blamed_lines:
                author_email = line['author-mail']
                if author_email != NO_AUTHOR_EMAIL:
                    authors.add(author_email)
        return authors

    def _get_line_numbers(self, region_set):
        """Get an line numbers for lines that overlap given RegionSet.
        :param empty_lines: Whether empty lines should be included
        :return: Set of 1-based line numbers
        """
        line_numbers = set()

        for region in region_set:
            lines = self.view.split_by_newlines(region)
            for line in lines:
                row_index, _ = self.view.rowcol(line.begin())
                line_numbers.add(row_index + 1)

        return line_numbers


# Git support

GIT_BLAME_FIELDS = (
    'author', 'author-mail', 'author-time', 'author-tz',
    'commiter', 'commiter-mail', 'committer-time', 'commiter-tz',
    'summary', 'previous', 'filename',
)
NO_AUTHOR_EMAIL = 'not.committed.yet'


def git_blame(filename, lines=None):
    flags = {}
    if lines is not None:
        flags['L'] = ','.join(map(str, lines))

    output = shell('git', 'blame', filename, line_porcelain=True, **flags)
    output_lines = output.splitlines()

    line_infos = []
    i = 0
    while i < len(output_lines):
        line_desc = output_lines[i:i+len(GIT_BLAME_FIELDS)+2]  # + hash + line
        line_info = {
            'hash': line_desc[0].split()[0],  # format: <hash> some numbers
            'line': line_desc[-1] .lstrip('\t'),
        }
        for field, row in izip(GIT_BLAME_FIELDS, line_desc[1:-1]):
            _, value = row.split(None, 1)
            if field == 'previous':
                value = value.split()[0]  # format: <hash> <filename>
            elif field.endswith('-mail'):
                value = value[1:-1]  # mails are in angle brackets; strip them
            line_info[field] = value

        line_infos.append(line_info)
        i += len(line_desc)

    return line_infos


# Utility functions

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

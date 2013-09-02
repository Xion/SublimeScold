"""
Git support.
"""
from itertools import izip

from scold.util import shell


BLAME_FIELDS = ('author', 'author-mail', 'author-time', 'author-tz',
                'commiter', 'commiter-mail', 'committer-time', 'commiter-tz',
                'summary', 'previous', 'filename')
NO_AUTHOR_EMAIL = 'not.committed.yet'


def blame(filename, lines=None):
    flags = {}
    if lines is not None:
        flags['L'] = ','.join(map(str, lines))

    output = shell('git', 'blame', filename, line_porcelain=True, **flags)
    output_lines = output.splitlines()

    line_infos = []
    i = 0
    while i < len(output_lines):
        line_desc = output_lines[i:i + len(BLAME_FIELDS) + 2]  # + hash + line
        line_info = {
            'hash': line_desc[0].split()[0],  # format: <hash> some numbers
            'line': line_desc[-1] .lstrip('\t'),
        }
        for field, row in izip(BLAME_FIELDS, line_desc[1:-1]):
            _, value = row.split(None, 1)
            if field == 'previous':
                value = value.split()[0]  # format: <hash> <filename>
            elif field.endswith('-mail'):
                value = value[1:-1]  # mails are in angle brackets; strip them
            line_info[field] = value

        line_infos.append(line_info)
        i += len(line_desc)

    return line_infos

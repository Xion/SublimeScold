"""
Git support.
"""
from scold.util import shell


BLAME_FIELDS = [
    'author', 'author-mail', 'author-time', 'author-tz',
    'committer', 'committer-mail', 'committer-time', 'committer-tz',
    'summary', 'previous', 'filename',
]
NO_AUTHOR_EMAIL = 'not.committed.yet'


def blame(filename, lines=None):
    """Obtain results of ``git blame`` for given file,
    optionally limited to specified range of lines.

    :param lines: Tuple of (start, end) line numbers
    :return: List of blame data for each line
    """
    flags = {}
    if lines is not None:
        flags['L'] = ','.join(map(str, lines))

    output = shell('git', 'blame', filename, line_porcelain=True, **flags)

    # Output consists of sections of rows, where each section
    # corresponds to single line in the source file (``filename``).
    #
    # Section starts with commit hash, ends with source line itself (indented).
    # In between, there are fields with values, separated by whitespace, e.g.::
    #
    #     author-mail coder@example.com
    #     author-tz +0200

    result = []
    line_info = {}
    for row in output.splitlines():
        if row.startswith('\t' ):
            line_info['line'] = row.lstrip('\t')
            result.append(line_info)
            line_info = {}
            continue

        head, tail = row.split(None, 1)
        if head in BLAME_FIELDS:
            field, value = head, tail
            if field == 'previous':
                value = value.split()[0]  # format: <hash> <filename>
            elif field.endswith('-mail'):
                value = value[1:-1]  # strip angle brackets around email
            line_info[field] = value
        else:
            line_info['hash'] = head

    return result

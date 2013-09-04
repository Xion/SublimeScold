"""
Main plugin module.
"""
# Live dependency reloading shim -- see ``scold._reloader`` for details.
RELOADER = 'scold._reloader'
import imp, sys
if RELOADER in sys.modules:
    imp.reload(sys.modules[RELOADER])
__import__(RELOADER)


import os

from sublime import error_message, message_dialog
from sublime_plugin import TextCommand

from scold import git
from scold.system import mailto
from scold.util import discrete_ranges


MAIL_SUBJECT = "WTF?"
MAIL_BODY = """
Dear Sir or Madam,

It came to my attention that in some unspecified time in the past,
you have managed to produce at least some fragments of the following:

{code}

I must hereby inform you that this... thing, which you may think of as "code",
is pretty much given to ellicit an emotional exclamation of bewilderment
from anyone required to read it -- including yours truly.

To put it other way, WTF is this?!

Sincerely,
Your Colleague
"""


class Scold(TextCommand):

    MAX_LINES_COUNT = 7

    def run(self, edit):
        if not self.view.file_name():
            message_dialog("Actually, it's you who wrote that...")
            return

        numbered_lines = self._get_selected_lines()
        authors = self._retrieve_authors(numbered_lines)
        if not authors:
            error_message("Can't find the author(s) of this fragment.")
            return

        # TODO: get the sender's name & email from Git config
        recipients = '; '.join(authors)
        body = self._compose_mail_body(numbered_lines)
        mailto(recipients, subject=MAIL_SUBJECT, body=body)

    def _get_selected_lines(self):
        """Get a list of numbers lines intersecting current selection.

        :return: List of "numbered lines": (index, line) tuples,
                 where ``index`` is 1-based index and ``line`` is a Region
        """
        numbered_lines = []

        line_indices = set()  # to remove lines duplicated across regions
        for region in self.view.sel():
            lines = self.view.lines(region)
            for line in lines:
                index, _ = self.view.rowcol(line.begin())
                if index not in line_indices:
                    line_indices.add(index)
                    numbered_lines.append((index + 1, line))

        return numbered_lines

    def _retrieve_authors(self, numbered_lines):
        """Retrieve the authors of text/code lines in current view.
        :param numbered_lines: List of "numbered lines"
        :return: Set of email addresses
        """
        filename = self.view.file_name()
        line_number_ranges = discrete_ranges(nr for (nr, _) in numbered_lines)

        authors = set()
        for line_range in line_number_ranges:
            blamed_lines = git.blame(filename, lines=line_range)
            for line in blamed_lines:
                author_email = line['author-mail']
                if author_email != git.NO_AUTHOR_EMAIL:
                    authors.add(author_email)

        return authors

    def _compose_mail_body(self, numbered_lines):
        """Format the mail body that includes numbered lines from current view.
        :param numbered_lines: List of "numbered lines"
        :return: Mail body
        """
        lines = [self.view.substr(region) for (_, region) in numbered_lines]

        overdue = len(lines) - self.MAX_LINES_COUNT
        if overdue > 0:
            ellipsis_text = "... and %s more such lines" % overdue
            lines[self.MAX_LINES_COUNT:] = [ellipsis_text]

        return MAIL_BODY.strip().format(code=os.linesep.join(lines))

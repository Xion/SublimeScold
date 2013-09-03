"""
Main plugin module.
"""
# Live dependency reloading shim -- see ``scold._reloader`` for details.
RELOADER = 'scold._reloader'
import imp, sys
if RELOADER in sys.modules:
    imp.reload(sys.modules[RELOADER])
__import__(RELOADER)


from sublime_plugin import TextCommand

from scold import git
from scold.system import mailto
from scold.util import discrete_ranges


MAIL_SUBJECT = "WTF?"
MAIL_BODY = """Dear Sir or Madam,

WTF is this?!

Sincerely,
Your Colleague
"""


class Scold(TextCommand):

    def run(self, edit):
        authors = self._get_selection_authors()
        if authors:
            # TODO: include offending piece of code in the mail
            recipients = '; '.join(authors)
            mailto(recipients, subject=MAIL_SUBJECT, body=MAIL_BODY)

    def _get_selection_authors(self):
        """Return the email addresses of authors of the current selection,
        as per the result of `git blame`.
        """
        filename = self.view.file_name()
        sel = self.view.sel()
        if not (filename and sel):
            return ()

        line_numbers = self._get_line_numbers(self.view.sel())
        line_ranges = discrete_ranges(line_numbers)

        authors = set()
        for line_range in line_ranges:
            blamed_lines = git.blame(filename, lines=line_range)
            for line in blamed_lines:
                author_email = line['author-mail']
                if author_email != git.NO_AUTHOR_EMAIL:
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

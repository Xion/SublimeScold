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

from sublime import error_message, load_settings, message_dialog
from sublime_plugin import TextCommand

from scold import git
from scold.system import mailto
from scold.util import discrete_ranges


class Scold(TextCommand):

    def __init__(self, *args, **kwargs):
        super(Scold, self).__init__(*args, **kwargs)
        self._settings = load_settings('Scold.sublime-settings')

    def run(self, edit):
        if not self.view.file_name():
            # TODO: detect the case where user (from `git config`) is also
            # the only author of the code (s)he wanted to critique
            message_dialog("Actually, it's you who wrote that...")
            return

        numbered_lines = self._get_selected_lines()
        authors = self._retrieve_authors(numbered_lines)
        if not authors:
            # TODO: distinguish different error cases:
            # no repository; untracked file; uncomitted change
            error_message("Can't find the author(s) of this fragment.")
            return

        # TODO: get the sender's name & email from Git config
        recipients = '; '.join(authors)
        subject = self._format_mail_subject(numbered_lines)
        body = self._compose_mail_body(numbered_lines)
        mailto(recipients, subject=subject, body=body)

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

        # TODO: remove empty or whitespace-only lines
        # at the beginning and end of selection
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

    def _format_mail_subject(self, numbered_lines):
        """Format the mail subject.
        :param numbered_lines: List of "numbered lines"
        :return: Mail subject
        """
        template = self._get_template('subject')
        if not template:
            return ""

        _, first_line = numbered_lines[0]
        return template.strip().format(line=first_line)

    def _compose_mail_body(self, numbered_lines):
        """Format the mail body that includes numbered lines from current view.
        :param numbered_lines: List of "numbered lines"
        :return: Mail body
        """
        template = self._get_template('body')
        if not template:
            return ""

        lines = [self.view.substr(region) for (_, region) in numbered_lines]
        overdue = len(lines) - self._max_lines_count
        if overdue > 0:
            ellipsis_text = "... and %s more such lines" % overdue
            lines[self._max_lines_count:] = [ellipsis_text]

        return template.strip().format(code=os.linesep.join(lines))

    def _get_template(self, kind):
        """Retrieve email subject or body template from settings."""
        template = self._settings.get('%s_template' % kind)
        if isinstance(template, list):
            template = os.linesep.join(template)
        return template

    @property
    def _max_lines_count(self):
        return self._settings.get('max_lines_count') or 10

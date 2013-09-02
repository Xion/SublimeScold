"""
Main plugin module.
"""
from sublime_plugin import TextCommand

from scold import git
from scold.util import discrete_ranges


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

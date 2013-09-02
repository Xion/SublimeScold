"""
Sublime Scold

Streamlines telling off your coworkers for lousy code.

:author: Karol Kuczmarski "Xion"
"""
from sublime_plugin import TextCommand


class Scold(TextCommand):

    def run(self, edit):
        self.view.insert(edit, 0, "Hello World")

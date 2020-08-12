from argparse import ArgumentParser
from typing import Dict, Tuple, List
import sys


class ModularParser:

    def __init__(self, **kwargs):
        self._parsers: Dict[str, Tuple[str, ArgumentParser, callable]] = dict()
        self.command_indent: int = 2
        self.command_help_length: int = 20
        self.space_after_command: int = 2
        self.terminal_line_lenght: int = 80
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise Exception(f"Unable to set {key} in {self.__class__}")

    def add_parser(self, module_name: str, about: str, parser: ArgumentParser, callback: callable) -> None:
        """
        Adds subpraser to modular parser.
        Args:
            module_name: subparser name displayed in help
            about: short description displayed next to name of subpraser
            parser: subparser
            callback: function that will be called with parser as it's argument
        """
        self._parsers[module_name] = (about, parser, callback)

    def parse_arguments(self, *args: str) -> None:
        """
        Parses arguments and calls associated callback.
        First argument (excluding script name) is name of module (subparser) where rest of arguments will be passed
        and which callback will be executed.
        Args:
            *arg: command args
        """
        print(f"Args: {args}")
        if len(args) >= 2 and args[1] in self._parsers.keys():
            _, subparser, callback = self._parsers[args[1]]
            parsed = subparser.parse_args(args[1:])
            callback(parsed)
            print(f"Parsing {args[1]} with {args[1:]}")
        elif len(args) == 1 or args[1] in ['-h', '--help']:
            self.draw_help()
        else:
            print(f"Error keyword: {args[1]}")
            self.draw_help()

    def draw_help(self):
        print(f"usage: fmiridenoise [-h | --help] <command> [<args>]")
        print("These are valid fmridenoise commands:")
        for key in self._parsers.keys():
            print(self._format_entry(key))

    def _format_entry(self, entry_name) -> str:
        about, _, _ = self._parsers[entry_name]
        string = (" " * self.command_indent + entry_name).ljust(self.command_indent + self.command_help_length)
        desc_start = self.command_indent + self.command_help_length
        desc_len = self.terminal_line_lenght - desc_start
        about_len = len(about)
        for start, stop in zip(range(0, about_len + 1, min(about_len, desc_len)), range(min(about_len, desc_len), about_len + 1, min(about_len, desc_len))):
            string += about[start:stop] + "\n" + " " * (self.command_indent + self.command_help_length)
        return string.strip()


if __name__ == '__main__':
    parser = ModularParser()
    parser.add_parser('test', 'long long long long long long long long long long long long long long long long long long long long long long long long long long long long long ', ArgumentParser(), lambda x: None)
    parser.add_parser('pierwsz', 'test description', ArgumentParser(), lambda x: None)
    parser.add_parser('drugi', 'test description', ArgumentParser(), lambda x: None)
    parser.parse_arguments(*sys.argv)
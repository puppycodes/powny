import sys

import tabloid
import colorama
import pygments
import pygments.lexers
import pygments.formatters

from ulib import ui
import ulib.ui.term  # pylint: disable=W0611

from . import tree


# =====
def print_config_dump(config, split_by, output=sys.stdout):
    table = tabloid.FormattedTable(
        width=ui.term.terminalSize(output=output)[0],
        header_background=colorama.Back.BLUE,
    )
    table.add_column("Option", _highlight_option)
    table.add_column("Value", _highlight_python)
    table.add_column("Default", _highlight_python)
    table.add_column("Help")

    for row in _make_plain_dump(config, tuple(map(tuple, split_by))):
        if row is None:
            table.add_row((" ") * 4)
        else:
            table.add_row(row)
    print("\n".join(table.get_table()), file=output)


def _highlight_option(name):
    if "!" in name:  # FIXME: crutch for tabloid
        name = name.replace("!", " ")
        return "{}{}{}".format(colorama.Fore.RED, name, colorama.Style.RESET_ALL)
    return name


def _highlight_python(code):
    if len(code) > 0:
        return pygments.highlight(
            code,
            pygments.lexers.PythonLexer(),
            pygments.formatters.TerminalFormatter(bg="dark"),
        ).replace("\n", "")
    else:
        return code


def _make_plain_dump(config, split_by=(), path=()):
    plain = []
    for (key, value) in config.items():
        if isinstance(value, tree.Section):
            if len(plain) != 0 and path in split_by:
                plain.append(None)
            plain += _make_plain_dump(value, split_by, path + (key,))
        else:
            default = config._get_default(key)  # pylint: disable=W0212
            changed = (default != value)
            plain.append((
                ".".join(path + (key,)).replace("_", "-") + ("!" if changed else ""),  # FIXME: crutch for tabloid
                repr(value),
                (repr(default) if changed else ""),
                config._get_help(key),  # pylint: disable=W0212
            ))
    return plain

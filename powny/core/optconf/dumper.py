import operator

import yaml

from . import Section


# =====
def make_config_dump(config):
    return "\n".join(_inner_make_dump(config))


def _inner_make_dump(config, path=()):
    lines = []
    for (key, value) in sorted(config.items(), key=operator.itemgetter(0)):
        indent = len(path) * "    "
        if isinstance(value, Section):
            lines.append("{}{}:".format(indent, key))
            lines += _inner_make_dump(value, path + (key,))
            lines.append("")
        else:
            default = config._get_default(key)  # pylint: disable=protected-access
            comment = config._get_help(key)  # pylint: disable=protected-access
            if default == value:
                lines.append("{}{}: {} # {}".format(indent, key, _make_yaml(value), comment))
            else:
                lines.append("{}# {}: {} # {}".format(indent, key, _make_yaml(default), comment))
                lines.append("{}{}: {}".format(indent, key, _make_yaml(value)))
    return lines


def _make_yaml(value):
    return yaml.dump(value, allow_unicode=True).replace("\n...\n", "").strip()

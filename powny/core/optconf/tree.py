import collections


# =====
class Section(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._meta = {}

    def _set_meta(self, name, secret, default, help):  # pylint: disable=redefined-builtin
        self._meta[name] = {
            "secret":  secret,
            "default": default,
            "help":    help,
        }

    def _is_secret(self, name):
        return self._meta[name]["secret"]

    def _get_default(self, name):
        return self._meta[name]["default"]

    def _get_help(self, name):
        return self._meta[name]["help"]

    def __getattribute__(self, name):
        if name in self:
            return self[name]
        else:  # For pickling
            return dict.__getattribute__(self, name)


Option = collections.namedtuple("Option", (
    "default",
    "type",
    "help",
))


class SecretOption(Option):
    pass

import collections


# =====
class Section(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._meta = {}
        self._secrets = []
        self._defaults = {}
        self._helps = {}

    def _set_meta(self, name, secret, default, help):  # pylint: disable=W0622
        self._meta[name] = (secret, default, help)

    def _is_secret(self, name):
        return self._meta[name][0]

    def _get_default(self, name):
        return self._meta[name][1]

    def _get_help(self, name):
        return self._meta[name][2]

    def __getattribute__(self, name):
        if name in self:
            return self[name]
        else:  # For pickling
            return dict.__getattribute__(self, name)


Option = collections.namedtuple("Option", (
    "default",
    "validator",
    "help",
))


class SecretOption(Option):
    pass

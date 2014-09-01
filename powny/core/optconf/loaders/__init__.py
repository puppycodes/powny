import copy

from ulib import typetools

from .. import tree


# =====
class ConfigLoader:
    def __init__(self, scheme, file_path, loader):
        self._scheme = copy.deepcopy(scheme)
        self._file_path = file_path
        self._loader = loader
        self._raw = {}

    def update_scheme(self, scheme):
        typetools.merge_dicts(self._scheme, scheme)

    def load(self):
        if self._file_path is not None:
            self._raw = self._loader(self._file_path)

    def get_config(self):
        return self._make_config(self._raw, self._scheme)

    def get_raw(self):
        return copy.deepcopy(self._raw)

    def _make_config(self, raw, scheme, keys=()):
        if not isinstance(raw, dict):
            raise ValueError("The node '{}' must be a dictionary".format(".".join(keys) or "/"))

        config = tree.Section()
        for (key, option) in scheme.items():
            raw_key = key.replace("_", "-")  # For yaml-file
            config_key = key.replace("-", "_")  # For result object
            long_key = keys + (raw_key,)
            long_name = ".".join(long_key)

            if isinstance(option, tree.Option):
                try:
                    value = option.validator(raw.get(raw_key, option.default))
                except ValueError as err:
                    raise ValueError("Invalid value of key '{}'".format(long_name)) from err
                config[config_key] = value
                config._set_meta(  # pylint: disable=W0212
                    name=config_key,
                    secret=isinstance(option, tree.SecretOption),
                    default=option.default,
                    help=option.help,
                )
            elif isinstance(option, dict):
                config[config_key] = self._make_config(raw.get(raw_key, {}), option, long_key)
            else:
                raise RuntimeError("Incorrect scheme definition for key '{}':"
                                   " the value is {}, not dict or [Secret]Option()".format(long_name, type(option)))
        return config

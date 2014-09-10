from .tree import Section
from .tree import Option
from .tree import SecretOption

from .dumper import make_config_dump
from .dumper import print_config_dump


# =====
def make_config(raw, scheme, keys=()):
    if not isinstance(raw, dict):
        raise ValueError("The node '{}' must be a dictionary".format(".".join(keys) or "/"))

    config = Section()
    for (key, option) in scheme.items():
        raw_key = key.replace("_", "-")  # For yaml-file
        config_key = key.replace("-", "_")  # For result object
        long_key = keys + (raw_key,)
        long_name = ".".join(long_key)

        if isinstance(option, Option):
            try:
                value = option.type(raw.get(raw_key, option.default))
            except ValueError as err:
                raise ValueError("Invalid value of key '{}'".format(long_name)) from err
            config[config_key] = value
            config._set_meta(  # pylint: disable=protected-access
                name=config_key,
                secret=isinstance(option, SecretOption),
                default=option.default,
                help=option.help,
            )
        elif isinstance(option, dict):
            config[config_key] = make_config(raw.get(raw_key, {}), option, long_key)
        else:
            raise RuntimeError("Incorrect scheme definition for key '{}':"
                               " the value is {}, not dict or [Secret]Option()".format(long_name, type(option)))
    return config

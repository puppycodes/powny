import os
import yaml
import yaml.loader

from contextlog import get_logger

from . import ConfigLoader


# =====
class YamlLoader(ConfigLoader):
    def __init__(self, scheme, file_path):
        ConfigLoader.__init__(self, scheme, file_path, _load_yaml)


# =====
def _load_yaml(file_path):
    with open(file_path) as yaml_file:
        get_logger().debug("Loading config from '%s'...", file_path)
        try:
            return yaml.load(yaml_file, _YamlLoader)
        except Exception as err:
            raise ValueError("Incorrect YAML syntax in file '{}'".format(file_path)) from err


class _YamlLoader(yaml.loader.Loader):
    def __init__(self, yaml_file):
        yaml.loader.Loader.__init__(self, yaml_file)
        self._root = os.path.dirname(yaml_file.name)

    def include(self, node):
        file_path = os.path.join(self._root, self.construct_scalar(node))  # pylint: disable=E1101
        get_logger().debug("Including config '%s'...", file_path)
        return _load_yaml(file_path)
_YamlLoader.add_constructor("!include", _YamlLoader.include)  # pylint: disable=E1101

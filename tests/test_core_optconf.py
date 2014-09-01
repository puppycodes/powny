# pylint: disable=R0904
# pylint: disable=W0212


import pytest

from powny.core import optconf
from powny.backends import zookeeper

from .fixtures.tmp import write_file


# =====
class TestYamlLoader:
    _scheme = {
        "key1": optconf.Option(default=1, validator=int, help=""),
        "key2": optconf.Option(default=2, validator=int, help=""),
        "section1": {
            "key11": optconf.Option(default=11, validator=float, help=""),
            "key12": optconf.Option(default=12, validator=float, help=""),
            "section2": {
                "key21": optconf.Option(default="21", validator=str, help=""),
            },
        },
    }

    def test_default(self):
        parser = optconf.YamlLoader(self._scheme, None)
        assert parser.get_raw() == {}
        config = parser.get_config()

        assert config.key1 == 1
        assert config.key2 == 2
        assert config.section1.key11 == 11.0
        assert config.section1.key12 == 12.0
        assert config.section1.section2.key21 == "21"

        def unpack(**kwargs):
            assert kwargs == {"key21": "21"}
        unpack(**config.section1.section2)

    def test_with_update(self):
        parser = optconf.YamlLoader(self._scheme, None)
        parser.load()
        parser.update_scheme({"backend": zookeeper.Backend.get_options()})
        config = parser.get_config()

        assert config.key1 == 1
        assert config.key2 == 2
        assert config.section1.key11 == 11.0
        assert config.section1.key12 == 12.0
        assert config.section1.section2.key21 == "21"

        assert config.backend.nodes == ["localhost"]
        assert config.backend.timeout == 10.0
        assert config.backend.start_timeout == 10.0
        assert config.backend.start_retries is None
        assert config.backend.randomize_hosts is True
        assert config.backend.chroot is None

    def test_with_include(self):
        with write_file("nodes:\n  - foo\n  - bar\nstart-retries: 1") as include_path:
            with write_file("core:\n  backend: zookeeper\nbackend: !include {}".format(include_path)) as main_path:
                parser = optconf.YamlLoader({
                    "core": {
                        "backend": optconf.Option(default="noop", validator=str, help=""),
                    },
                }, main_path)
                parser.load()
                assert parser.get_raw()["backend"]["nodes"] == ["foo", "bar"]
                assert parser.get_config().core.backend == "zookeeper"

                parser.update_scheme({"backend": zookeeper.Backend.get_options()})
                config = parser.get_config()
                assert config.backend.nodes == ["foo", "bar"]
                assert config.backend.timeout == 10.0

    def test_yaml_root_error(self):
        with write_file("foobar") as path:
            parser = optconf.YamlLoader(self._scheme, path)
            parser.load()
            with pytest.raises(ValueError):
                parser.get_config()

    def test_yaml_syntax_error(self):
        with write_file("&") as path:
            parser = optconf.YamlLoader(self._scheme, path)
            with pytest.raises(ValueError):
                parser.load()

    def test_yaml_invalid_value(self):
        with write_file("key1: x") as path:
            parser = optconf.YamlLoader(self._scheme, path)
            parser.load()
            with pytest.raises(ValueError):
                parser.get_config()

    def test_yaml_not_a_section(self):
        with write_file("section1: 5") as path:
            parser = optconf.YamlLoader(self._scheme, path)
            parser.load()
            with pytest.raises(ValueError):
                parser.get_config()

    def test_invalid_scheme(self):
        parser = optconf.YamlLoader({"foo": "bar"}, None)
        with pytest.raises(RuntimeError):
            parser.get_config()

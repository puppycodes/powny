# pylint: disable=redefined-outer-name


import pytest

from ulib import typetools

from powny.core import optconf
from powny.core.optconf.loaders import yaml
from powny.testing.tmpfile import write_file
from powny.backends import zookeeper


# =====
@pytest.fixture
def scheme():
    return {
        "key1": optconf.Option(default=1, type=int, help=""),
        "key2": optconf.Option(default=2, type=int, help=""),
        "section1": {
            "key11": optconf.Option(default=11, type=float, help=""),
            "key12": optconf.Option(default=12, type=float, help=""),
            "section2": {
                "key21": optconf.Option(default="21", type=str, help=""),
            },
        },
    }


class TestLoadFromYaml:
    def test_default(self, scheme):
        config = optconf.make_config({}, scheme)

        assert config.key1 == 1
        assert config.key2 == 2
        assert config.section1.key11 == 11.0
        assert config.section1.key12 == 12.0
        assert config.section1.section2.key21 == "21"

        def unpack(**kwargs):
            assert kwargs == {"key21": "21"}
        unpack(**config.section1.section2)

    def test_with_update(self, scheme):
        typetools.merge_dicts(scheme, {"backend": zookeeper.Backend.get_options()})
        config = optconf.make_config({}, scheme)

        assert config.key1 == 1
        assert config.key2 == 2
        assert config.section1.key11 == 11.0
        assert config.section1.key12 == 12.0
        assert config.section1.section2.key21 == "21"

        assert config.backend.nodes == ["localhost:2181"]
        assert config.backend.timeout == 10.0
        assert config.backend.start_timeout == 10.0
        assert config.backend.start_retries == 1
        assert config.backend.randomize_hosts is True
        assert config.backend.chroot is None

    def test_with_include(self):
        with write_file("nodes:\n  - foo\n  - bar\nstart-retries: 1") as include_path:
            with write_file("core:\n  backend: zookeeper\nbackend: !include {}".format(include_path)) as main_path:
                raw = yaml.load_file(main_path)
                scheme = {
                    "core": {
                        "backend": optconf.Option(default="noop", type=str, help=""),
                    },
                }
                config = optconf.make_config(raw, scheme)
                assert raw["backend"]["nodes"] == ["foo", "bar"]
                assert config.core.backend == "zookeeper"

                typetools.merge_dicts(scheme, {"backend": zookeeper.Backend.get_options()})
                config = optconf.make_config(raw, scheme)
                assert config.backend.nodes == ["foo", "bar"]
                assert config.backend.timeout == 10.0

    def test_yaml_root_error(self, scheme):
        with write_file("foobar") as path:
            raw = yaml.load_file(path)
            with pytest.raises(ValueError):
                optconf.make_config(raw, scheme)

    def test_yaml_syntax_error(self):
        with write_file("&") as path:
            with pytest.raises(ValueError):
                yaml.load_file(path)

    def test_yaml_invalid_value(self, scheme):
        with write_file("key1: x") as path:
            raw = yaml.load_file(path)
            with pytest.raises(ValueError):
                optconf.make_config(raw, scheme)

    def test_yaml_not_a_section(self, scheme):
        with write_file("section1: 5") as path:
            raw = yaml.load_file(path)
            with pytest.raises(ValueError):
                optconf.make_config(raw, scheme)

    def test_invalid_scheme(self):
        with pytest.raises(RuntimeError):
            optconf.make_config({}, {"foo": "bar"})

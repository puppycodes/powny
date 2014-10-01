from powny.core import apps


# =====
class TestService:
    def teardown_method(self, _):
        apps._config = None  # pylint: disable=protected-access

    def test_init_and_get_config(self):
        config = apps.init("test_init", "TestService", [])
        assert config.core.backend == "zookeeper"
        assert config.backend.nodes == ["localhost:2181"]
        assert apps.get_config() == config

import os
import contextlib
import pprint

from powny.core import imprules

from .fixtures.tmp import write_tree


# =====
@contextlib.contextmanager
def _loader(module_base, group_by=None):
    loader = imprules.Loader(module_base, group_by)
    yield loader

def _make_defines(value):
    expose = "from powny.core.imprules import expose\n"
    return (
        ("rules/__init__.py",     expose + "@expose\ndef foo(): pass"),
        ("rules/sub/__init__.py", expose + "@expose\ndef bar(): pass"),
        ("rules/sub/rule.py",     expose + "from .module import X\n@expose\ndef baz(): return X"),
        ("rules/sub/module.py",   "X = {}\ndef method(): pass".format(value)),
        ("rules/sub/hlr.py",      expose + "@expose\ndef handler(): pass"),
        ("rules/sub/failed.py",   "print(os)"),
    )


# =====
class TestImpRules:
    _names = [
        "powny",
        "powny.backends",
        "powny.backends.zookeeper",
        "powny.backends.zookeeper.ifaces",
        "powny.backends.zookeeper.zoo",
        "powny.core",
        "powny.core.api",
        "powny.core.api.jobs",
        "powny.core.api.rules",
        "powny.core.api.system",
        "powny.core.apps",
        "powny.core.apps.api",
        "powny.core.apps.collector",
        "powny.core.apps.worker",
        "powny.core.backends",
        "powny.core.context",
        "powny.core.imprules",
        "powny.core.optconf",
        "powny.core.optconf.dumper",
        "powny.core.optconf.loaders",
        "powny.core.optconf.loaders.yaml",
        "powny.core.optconf.tree",
        "powny.core.rules",
        "powny.core.tools",
        "powny.helpers",
        "powny.helpers.cmp",
        "powny.helpers.email",
        "powny.helpers.hipchat",
        "setup",
        "tests",
        "tests.fixtures",
        "tests.fixtures.application",
        "tests.fixtures.context",
        "tests.fixtures.tmp",
        "tests.fixtures.zookeeper",
        "tests.test_backends_zookeeper",
        "tests.test_backends_zookeeper_ifaces",
        "tests.test_backends_zookeeper_zoo",
        "tests.test_core_apps",
        "tests.test_core_backends",
        "tests.test_core_context",
        "tests.test_core_imprules",
        "tests.test_core_optconf",
        "tests.test_core_rules",
        "tests.test_core_tools",
        "tests.test_helpers_cmp",
        "tests.test_helpers_email",
        "tests.test_helpers_hipchat",
        "tests.test_powny",
    ]

    def test_expose(self):
        @imprules.expose
        def foobar():
            pass
        assert getattr(foobar, imprules._ATTR_EXPOSED)  # pylint: disable=protected-access

    def test_get_all_modules_rel(self):
        names = imprules._get_all_modules(".")  # pylint: disable=protected-access
        pprint.pprint(names)
        assert names == self._names

    def test_get_all_modules_cwd(self):
        names = imprules._get_all_modules(os.getcwd())  # pylint: disable=protected-access
        pprint.pprint(names)
        assert names == self._names


class TestLoader:
    def test_loader_replace(self):
        defined = set((
            "rules.foo",
            "rules.sub.bar",
            "rules.sub.rule.baz",
            "rules.sub.hlr.handler",
        ))
        failed = set(("rules.sub.failed",))

        with _loader("rules") as loader:
            with write_tree(_make_defines(1)) as root:
                (methods_1, errors_1) = loader.get_exposed(root)
                assert set(methods_1) == defined
                assert set(errors_1) == failed
                assert "rules.sub.module.method" not in methods_1
                (methods_1_cached, errors_1_cached) = loader.get_exposed(root)
                assert methods_1 == methods_1_cached
                assert errors_1 == errors_1_cached

            with write_tree(_make_defines(2)) as root:
                (methods_2, errors_2) = loader.get_exposed(root)
                assert set(methods_2) == defined
                assert set(errors_2) == failed
                assert "rules.sub.module.method" not in methods_2
                (methods_2_cached, errors_2_cached) = loader.get_exposed(root)
                assert methods_2 == methods_2_cached
                assert errors_2 == errors_2_cached

            assert set(methods_1.values()) != set(methods_2.values())
            assert methods_1["rules.sub.rule.baz"]() == 1
            assert methods_2["rules.sub.rule.baz"]() == 2

    def test_loader_group_by(self):
        group_by = (
            ("handlers", lambda method: method.__name__.endswith("handler")),
            ("other",    lambda _: True),
        )
        with _loader("rules", group_by) as loader:
            with write_tree(_make_defines(1)) as root:
                (methods, _) = loader.get_exposed(root)
                assert set(methods) == set(("handlers", "other"))

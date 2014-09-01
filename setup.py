import setuptools


# =====
if __name__ == "__main__":
    setuptools.setup(
        name="powny",
        version="1.0",
        url="https://github.com/yandex-sysmon/powny",
        license="GPLv3",
        author="Devaev Maxim",
        author_email="mdevaev@gmail.com",
        description="Distributed events processor, based on stackless technology of PyPy3",
        platforms="any",

        packages=[
            "powny",
            "powny.core",
            "powny.core.api",
            "powny.core.apps",
            "powny.core.optconf",  # TODO: Make a separate package
            "powny.core.optconf.loaders",
            "powny.backends.zookeeper",
            "powny.helpers.cmp",
            "powny.helpers.email",
            "powny.helpers.hipchat",
        ],

        package_data={
            "powny.core.api": ["templates/*.html"],
            "powny.core.apps": ["configs/*.yaml"],
        },

        namespace_packages=[
            "powny",
            "powny.backends",
            "powny.helpers",
        ],

        entry_points={
            "console_scripts": [
                "powny-api = powny.core.apps.api:run",
                "powny-worker = powny.core.apps.worker:run",
                "powny-collector = powny.core.apps.collector:run",
            ]
        },

        classifiers=[  # http://pypi.python.org/pypi?:action=list_classifiers
            "Development Status :: 4 - Beta",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Operating System :: POSIX :: Linux",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: Implementation :: PyPy",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: System :: Distributed Computing",
            "Topic :: System :: Networking :: Monitoring",
        ],

        install_requires=[
            "kazoo.yandex",
            "pyyaml.yandex",
            "Flask-API.yandex",
            "ulib",
            "decorator",
            "contextlog",
            "colorlog",
            "pkginfo",

            # Optconf
            "Tabloid",
            "colorama",
            "pygments",

            # Helpers
            "requests <= 2.3.0",  # FIXME: https://github.com/kevin1024/vcrpy/issues/94
        ],
    )

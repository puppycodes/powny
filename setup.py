import setuptools


# =====
if __name__ == "__main__":
    setuptools.setup(
        name="powny",
        version="4.5.0",
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
            "powny.backends",
            "powny.backends.zookeeper",
            "powny.testing",
        ],

        package_data={
            "powny.core.api": ["templates/*.html"],
            "powny.core.apps": ["configs/*.yaml"],
        },

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
            "kazoo",
            "Flask-API",
            "python-dateutil",
            "gunicorn",
            "pyyaml",
            "decorator",
            "contextlog",
            "colorlog",
            "setproctitle",

            # Backdoor
            "manhole",

            # Optconf
            "colorama",
            "pygments",
        ],
    )

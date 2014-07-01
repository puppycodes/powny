#!/usr/bin/env python


import setuptools


##### Main #####
if __name__ == "__main__":
    setuptools.setup(
        name="gns",
        version="0.2",
        url="https://github.com/yandex-sysmon/gns",
        license="GPLv3",
        author="Devaev Maxim",
        author_email="mdevaev@gmail.com",
        description="Universal distributed notification service",
        platforms="any",

        packages=(
            "gns",
            "gns/api",
        ),

        entry_points={
            "console_scripts": [
                "gns = gns.cli:main",
            ]
        },

        classifiers=[ # http://pypi.python.org/pypi?:action=list_classifiers
            "Development Status :: 2 - Pre-Alpha",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Operating System :: POSIX :: Linux",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: Implementation :: PyPy",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: System :: Distributed Computing",
            "Topic :: System :: Networking :: Monitoring",
        ],

        install_requires=[
            "raava >= 0.16",
            "elog >= 0.4",
            "chrpc >= 0.1",
            "meters >= 0.3",
            "gns-helpers >= 0.1",

            "ulib >= 0.24",
            "pyyaml >= 3.10",
            "decorator >= 3.4.0",
            "manhole >= 0.6.1",
            "objgraph >= 1.8.1",
            "membug >= 0.1",
        ],
    )

#!/usr/bin/env python


import setuptools


##### Main #####
if __name__ == "__main__":
    setuptools.setup(
        name="gns",
        version="0.1",
        url="https://github.com/yandex-sysmon/gns",
        license="GPLv3",
        author="Devaev Maxim",
        author_email="mdevaev@gmail.com",
        description="Universal distributed notification service",
        platforms="any",

        packages=(
            "gns",
            "gns/api",
            "gns/fetchers",
        ),

        entry_points={
            "console_scripts": [
                "gns = gns.cli:main",
                "gns-rpc = gns.client:main",
            ]
        },

        classifiers=( # http://pypi.python.org/pypi?:action=list_classifiers
            "Development Status :: 2 - Pre-Alpha",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Operating System :: POSIX :: Linux",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: Implementation :: PyPy",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: System :: Distributed Computing",
            "Topic :: System :: Networking :: Monitoring",
        ),

        install_requires=(
            "raava == 0.3",
            "elog >= 0.1",
            "chrpc >= 0.1",
            "meters >= 0.3",

            "kazoo >= 1.3.1",
            "ulib >= 0.24",
            "pyyaml >= 3.10",
            "decorator >= 3.4.0",
            "python-dateutil >= 2.2",
        ),
    )


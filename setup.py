#!/usr/bin/env pypy3


import os
import setuptools
import distutils.command.build
import textwrap
import gns.const


##### Public constants #####
ETC_DIR    = "/etc"
USRLIB_DIR = "/usr/lib"
VARLIB_DIR = "/var/lib"


##### Public classes #####
class GnsBuild(distutils.command.build.build):
    def run(self):
        distutils.command.build.build.run(self)
        self._write_lib("gns", "const_site.py", """
                CONFIG_FILE = "%(etc)s/gns/gns.conf"
                RULES_DIR   = "%(varlib)s/gns/rules"
            """ % {
                "etc":    ETC_DIR,
                "varlib": VARLIB_DIR,
            })

    def _write_lib(self, module, file_name, text):
        file_path = os.path.join(self.build_lib, module, file_name)
        assert os.path.getsize(file_path) == 0
        with open(file_path, "w") as lib_file:
            lib_file.write(textwrap.dedent(text).strip())


##### Main #####
if __name__ == "__main__":
    setuptools.setup(
        name="gns",
        version=gns.const.VERSION,
        url=gns.const.UPSTREAM_URL,
        license="GPLv3",
        author="Devaev Maxim",
        author_email="mdevaev@gmail.com",
        description="Useful python library",
        platforms="any",

        packages=(
            "gns",
            "raava",
            "raava/apps",
        ),

        data_files=(
            (USRLIB_DIR + "/gns", (
                    "splitter.py",
                    "worker.py",
                    "collector.py",
                    "cli.py",
                    "reinit.py",
                    "demo-api.py",
                )),
        ),

        classifiers=( # http://pypi.python.org/pypi?:action=list_classifiers
            "Development Status :: 2 - Pre-Alpha",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Operating System :: POSIX :: Linux",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: Implementation :: PyPy"
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: System :: Distributed Computing",
            "Topic :: System :: Networking :: Monitoring",
        ),

        install_requires=(
            "kazoo >= 1.3.1",
            "ulib >= 0.17",
        )

        cmdclass = { "build": GnsBuild },
    )


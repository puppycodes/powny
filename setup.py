#!/usr/bin/env python


import os
import setuptools
import distutils.command.build
import textwrap
import gns.const


##### Public constants #####
ETC_DIR    = "/etc"
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
        description="Universal distributed notification service",
        platforms="any",

        packages=(
            "gns",
            "grpc",
            "raava",
            "raava/apps",
        ),

        scripts=(
            "gns-splitter.py",
            "gns-worker.py",
            "gns-collector.py",
            "gns-cli.py",
            "gns-reinit.py",
            "gns-api.py",
        ),

        package_data={
            "grpc": ["templates/*.html"],
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
            "kazoo >= 1.3.1",
            "ulib >= 0.19",
            "cherrypy >= 3.2.4",
            "mako >= 0.9.1",
            "decorator >= 3.4.0",
        ),

        cmdclass = { "build": GnsBuild },
    )


import os
import subprocess
import shutil
import pygit2
import logging

from ulib import validators
import ulib.validators.common # pylint: disable=W0611
import ulib.validators.fs

from .. import service


##### Public constants #####
LOGGER_NAME = "git"


###
S_GIT = "git"

O_REPO_URL  = "repo-url"
O_REPO_DIR  = "repo-dir"
O_REVISIONS = "revisions"
O_GIT_BIN   = "git-bin"
O_TAR_BIN   = "tar-bin"
O_PREFIX    = "prefix"


##### Private objects #####
_logger = logging.getLogger(LOGGER_NAME)


##### Private methods #####
def _shell_exec(args):
    _logger.debug("Running the command: %s", args)
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={ "LC_ALL": "C" },
        shell=True,
    )
    (proc_stdout, proc_stderr) = proc.communicate()
    proc_retcode = proc.returncode
    message = "Command \"{cmd}\" results:\nStdout: {stdout}\nStderr: {stderr}\nReturn code: {retcode}".format(
        cmd=args,
        stdout=proc_stdout.strip(),
        stderr=proc_stderr.strip(),
        retcode=proc_retcode,
    )
    if proc_retcode != 0:
        _logger.error(message)
        raise RuntimeError("Command error")
    else:
        _logger.debug(message)

def _git_cleanup(rules_path, prefix, modules_list):
    for module_name in os.listdir(rules_path):
        if not module_name.startswith(prefix):
            continue
        if not module_name in modules_list:
            _logger.info("Removing the old module: %s", module_name)
            shutil.rmtree(os.path.join(rules_path, module_name))

def _git_update_rules(config_dict):
    _shell_exec("{git} -C {repo} pull".format(
            git=config_dict[S_GIT][O_GIT_BIN],
            repo=config_dict[S_GIT][O_REPO_DIR],
        ))
    repo = pygit2.Repository(config_dict[S_GIT][O_REPO_DIR])

    rules_path = config_dict[service.S_CORE][service.O_RULES_DIR]
    prefix = config_dict[S_GIT][O_PREFIX]

    modules_list = []
    revisions = config_dict[S_GIT][O_REVISIONS]
    for commit in repo.walk(repo.head.get_object().id, pygit2.GIT_SORT_NONE):
        if revisions == 0:
            break
        revisions -= 1

        module_name = prefix + commit.id.hex
        modules_list.append(module_name)

        module_path = os.path.join(rules_path, module_name)
        if os.path.exists(module_path):
            continue

        tmp_path = os.path.join(rules_path, "." + module_name)
        if os.path.exists(tmp_path):
            shutil.rmtree(tmp_path)
        os.mkdir(tmp_path)

        _logger.info("Checkout %s --> %s", commit.id.hex, module_path)
        _shell_exec("{git} -C {repo} archive {commit} | {tar} -x -C {tmp}".format(
                git=config_dict[S_GIT][O_GIT_BIN],
                repo=config_dict[S_GIT][O_REPO_DIR],
                commit=commit.id,
                tar=config_dict[S_GIT][O_TAR_BIN],
                tmp=tmp_path,
            ))
        os.rename(tmp_path, module_path)

    _git_cleanup(rules_path, prefix, modules_list)

    return prefix + repo.head.get_object().id.hex


##### Public constants #####
CONFIG_MAP = {
    S_GIT: {
        O_REPO_URL:  ("http://example.com", str),
        O_REPO_DIR:  ("/tmp",               lambda arg: validators.fs.valid_accessible_path(arg + "/.")),
        O_REVISIONS: (10,                   lambda arg: validators.common.valid_number(arg, 1)),
        O_GIT_BIN:   ("/usr/bin/git",       validators.fs.valid_accessible_path),
        O_TAR_BIN:   ("/usr/bin/tar",       validators.fs.valid_accessible_path),
        O_PREFIX:    ("git_",               str),
    },
}

FETCHERS_MAP = {
    "git": _git_update_rules,
}


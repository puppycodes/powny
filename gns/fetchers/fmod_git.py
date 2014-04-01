import os
import subprocess
import shutil
import logging

from ulib import validators
import ulib.validators.common # pylint: disable=W0611
import ulib.validators.fs

from .. import service


##### Public constants #####
S_GIT = "git"

O_REPO_URL  = "repo-url"
O_REPO_DIR  = "repo-dir"
O_REVISIONS = "revisions"
O_PREFIX    = "prefix"


##### Private objects #####
_logger = logging.getLogger(__name__)


##### Private methods #####
def _shell_exec(command, **kwargs):
    proc_stdout = subprocess.check_output(
        command.format(**kwargs),
        env={ "LC_ALL": "C" },
        universal_newlines=True,
        shell=True,
    )
    _logger.debug("Command stdout:\n{}".format(proc_stdout))
    return proc_stdout

def _git_cleanup(rules_path, prefix, modules):
    for module_name in os.listdir(rules_path):
        if not module_name.startswith(prefix):
            continue
        if not module_name in modules:
            _logger.info("Removing the old module: %s", module_name)
            shutil.rmtree(os.path.join(rules_path, module_name))

def _git_update_rules(config):
    git_worktree = config[S_GIT][O_REPO_DIR]
    git_dir = os.path.join(git_worktree, ".git")
    if not os.path.exists(git_dir):
        _logger.info("git dir %s does not exist", git_dir)
        repo_url = config[S_GIT].get(O_REPO_URL)
        if repo_url:
            _logger.info("initializing git repo %s with remote %s", git_worktree, repo_url)
            _shell_exec("git clone {url} {git_worktree}", git_worktree=git_worktree, url=repo_url)
        else:
            raise RuntimeError("git dir {} does not exist and {}.{} is not set".format(git_dir, S_GIT, O_REPO_URL))
    _shell_exec("git --work-tree {git_worktree} --git-dir {git_dir} pull", git_worktree=git_worktree, git_dir=git_dir)

    rules_path = config[service.S_CORE][service.O_RULES_DIR]
    prefix = config[S_GIT][O_PREFIX]

    modules = []
    commits = _shell_exec("git --work-tree {git_worktree} --git-dir {git_dir} log -n {limit} --pretty=format:%H",
        git_worktree=git_worktree,
        git_dir=git_dir,
        limit=config[S_GIT][O_REVISIONS],
    ).strip().split("\n")
    assert len(commits) > 0
    for commit in commits:
        module_name = prefix + commit
        modules.append(module_name)

        module_path = os.path.join(rules_path, module_name)
        if os.path.exists(module_path):
            continue

        tmp_path = os.path.join(rules_path, "." + module_name)
        if os.path.exists(tmp_path):
            shutil.rmtree(tmp_path)
        os.mkdir(tmp_path)

        _logger.info("Checkout %s --> %s", commit, module_path)
        _shell_exec("git --work-tree {git_worktree} --git-dir {git_dir} archive {commit} | tar -x -C {tmp}",
            git_worktree=git_worktree,
            git_dir=git_dir,
            commit=commit,
            tmp=tmp_path,
        )
        os.rename(tmp_path, module_path)

    _git_cleanup(rules_path, prefix, modules)

    return prefix + commits[0]


##### Public constants #####
CONFIG_MAP = {
    S_GIT: {
        O_REPO_URL:  ("http://example.com", str),
        O_REPO_DIR:  ("/tmp",               lambda arg: validators.fs.valid_accessible_path(arg + "/.")),
        O_REVISIONS: (10,                   lambda arg: validators.common.valid_number(arg, 1)),
        O_PREFIX:    ("git_",               str),
    },
}

FETCHERS_MAP = {
    "git": _git_update_rules,
}


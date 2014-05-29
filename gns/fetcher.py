#!/usr/bin/env python


import os
import subprocess
import shutil
import logging
import time

from . import service


##### Private objects #####
_logger = logging.getLogger(__name__)


##### Public methods #####
def run(config):
    interval = config[service.S_CORE][service.O_FETCH_INTERVAL]
    if interval == 0:
        try:
            _update_rules(config)
        except Exception:
            _logger.exception("Exception while rules fetching")
            raise
    else:
        # FIXME: this code is added to provide a way to run periodic task inside a container.
        # running cron or systemd timer is a better solution, but it demands additional research.
        _logger.info("Starting periodic rules fetching each %d seconds", interval)
        while True:
            next_fetch = time.time() + interval
            try:
                _update_rules(config)
            except (SystemExit, KeyboardInterrupt):
                break # No traceback for this.
            except Exception:
                _logger.exception("Exception while rules fetching")
            time.sleep(next_fetch - time.time())
        _logger.info("Stopped rules fetching")


##### Private methods #####
def _update_rules(config):
    git_worktree   = config[service.S_GIT][service.O_REPO_DIR]
    repo_url       = config[service.S_GIT][service.O_REPO_URL]
    rules_path     = config[service.S_CORE][service.O_RULES_DIR]
    head_name      = config[service.S_CORE][service.O_RULES_HEAD]
    prefix         = config[service.S_GIT][service.O_PREFIX]
    keep_revisions = config[service.S_GIT][service.O_REVISIONS]

    _git_pull(git_worktree, repo_url)
    (module_name, keep_modules) = _git_update_rules(git_worktree, rules_path, prefix, keep_revisions)
    _replace_head(rules_path, head_name, module_name)
    _git_cleanup(rules_path, prefix, keep_modules)

def _replace_head(rules_path, head_name, module_name):
    head_path = os.path.join(rules_path, head_name)
    if os.path.islink(head_path) and os.readlink(head_path) == module_name:
        _logger.debug("HEAD does not need to be updated")
        return
    tmp_path = os.path.join(rules_path, module_name + ".tmp")
    _logger.info("Updating the rules HEAD to %s", module_name)
    os.symlink(module_name, tmp_path)
    try:
        os.rename(tmp_path, head_path)
    except Exception:
        _logger.exception("Cannot rewrite the HEAD symlink")
        os.unlink(tmp_path)
        raise


###
def _git_pull(git_worktree, repo_url):
    git_dir = os.path.join(git_worktree, ".git")
    if not os.path.exists(git_dir):
        _logger.info("git dir %s does not exist", git_dir)
        if len(repo_url) != 0:
            _logger.info("initializing git repo %s with remote %s", git_worktree, repo_url)
            _shell_exec("git clone {url} {git_worktree}".format(git_worktree=git_worktree, url=repo_url))
        else:
            raise RuntimeError("git dir {} does not exist and repo-url is not set".format(git_dir))
    _shell_exec("git pull", cwd=git_worktree)

def _git_update_rules(git_worktree, rules_path, prefix, keep_revisions):
    keep_modules = []
    commits = _shell_exec("git log -n {} --pretty=format:%H".format(keep_revisions), cwd=git_worktree)
    commits = commits.strip().split("\n")
    assert len(commits) > 0

    for commit in commits:
        module_name = prefix + commit
        keep_modules.append(module_name)

        module_path = os.path.join(rules_path, module_name)
        if os.path.exists(module_path):
            continue

        tmp_path = os.path.join(rules_path, "." + module_name)
        if os.path.exists(tmp_path):
            shutil.rmtree(tmp_path)
        os.mkdir(tmp_path)

        _logger.info("Checkout %s --> %s", commit, module_path)
        try:
            _shell_exec("git clone {git_worktree} {tmp}".format(git_worktree=git_worktree, tmp=tmp_path))
            _shell_exec("git checkout -b version-{commit} {commit}".format(commit=commit), cwd=tmp_path)
            _shell_exec("git submodule init", cwd=tmp_path)
            _shell_exec("git submodule update", cwd=tmp_path)
            os.rename(tmp_path, module_path)
        except Exception:
            _logger.exception("Unable to checkout %s", commit)

    return (prefix + commits[0], keep_modules)


def _git_cleanup(rules_path, prefix, keep_modules):
    for module_name in os.listdir(rules_path):
        if not module_name.startswith(prefix):
            continue
        if not module_name in keep_modules:
            _logger.info("Removing the old module: %s", module_name)
            shutil.rmtree(os.path.join(rules_path, module_name))

def _shell_exec(command, cwd=None):
    proc_stdout = subprocess.check_output(
        command,
        env={ "LC_ALL": "C" },
        universal_newlines=True,
        shell=True,
        cwd=cwd,
    )
    _logger.debug("Command '{}' stdout:\n{}".format(command, proc_stdout))
    return proc_stdout

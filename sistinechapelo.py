import os
import logging
import subprocess


class Dot(dict): # dot notation access to dictionary attributes
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


log = logging.getLogger("sistinechapel")
quick_allowed = True
errors = 0
opts = {}
args = Dot({
    'debug': False,
    'reset': False,
    'upgrade': False,
    'skip_update': False,
    'skip_extensions': False,
    'skip_requirements': False,
    'skip_git': False,
    'skip_torch': False,
    'use_directml': False,
    'use_ipex': False,
    'use_cuda': False,
    'use_rocm': False,
    'experimental': False,
    'test': False,
    'tls_selfsign': False,
    'reinstall': False,
    'version': False,
    'ignore': False,
})

# execute git command
def git(arg: str, folder: str = None, ignore: bool = False):
    if args.skip_git:
        return ''
    git_cmd = os.environ.get('GIT', "git")
    result = subprocess.run(f'"{git_cmd}" {arg}', check=False, shell=True, env=os.environ, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=folder or '.')
    txt = result.stdout.decode(encoding="utf8", errors="ignore")
    if len(result.stderr) > 0:
        txt += ('\n' if len(txt) > 0 else '') + result.stderr.decode(encoding="utf8", errors="ignore")
    txt = txt.strip()
    if result.returncode != 0 and not ignore:
        global errors # pylint: disable=global-statement
        errors += 1
        log.error(f'Error running git: {folder} / {arg}')
        if 'or stash them' in txt:
            log.error('Local changes detected: check setup.log for details')
        log.debug(f'Git output: {txt}')
    return txt

# clone git repository
def clone(url, folder, commithash=None):
    if os.path.exists(folder):
        if commithash is None:
            git('pull', folder)
        # current_hash = git('rev-parse HEAD', folder).strip()
        # if current_hash != commithash:
        #     git('fetch', folder)
        #     git(f'checkout {commithash}', folder)
        #     return
    else:
        git(f'clone "{url}" "{folder}"')
        if commithash is not None:
            git(f'-C "{folder}" checkout {commithash}')

# clone required repositories
def install_repositories():
    def d(name):
        return os.path.join(os.path.dirname(__file__), 'cmfy', name)
    log.info('Installing sistinechapel')
    os.makedirs(os.path.join(os.path.dirname(__file__), 'cmfy'), exist_ok=True)
    sistinechapel_repo = os.environ.get('SISTINE_CHAPEL_REPO', "https://github.com/comfyanonymous/ComfyUI.git")
    
    clone(sistinechapel_repo, d('sistinechapel'))


def run_setup():
    install_repositories()

if __name__ == "__main__":
    run_setup()

import os
import logging
import subprocess


class Dot(dict): # dot notation access to dictionary attributes
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


log = logging.getLogger("sd")
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
        return os.path.join(os.path.dirname(__file__), 'photon', name)
    log.info('Installing photon cannon')
    os.makedirs(os.path.join(os.path.dirname(__file__), 'photon'), exist_ok=True)
    chapel_repo = os.environ.get('PHOTON_REPO', "https://github.com/lllyasviel/stable-diffusion-webui-forge.git")
    #sistinechapel_commit = os.environ.get('CHAPEL_REPO_REPO_COMMIT_HASH', "5ab7f213bec2f816f9c5644becb32eb72c8ffb89")
    clone(chapel_repo, d('cannon'))

# set environment variables controling the behavior of various libraries
def set_environment():
    log.info('Setting environment tuning')
    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
    os.environ.setdefault('ACCELERATE', 'True')
    os.environ.setdefault('FORCE_CUDA', '1')
    os.environ.setdefault('ATTN_PRECISION', 'fp16')
    os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF', 'garbage_collection_threshold:0.8,max_split_size_mb:512')
    os.environ.setdefault('CUDA_LAUNCH_BLOCKING', '0')
    os.environ.setdefault('CUDA_CACHE_DISABLE', '0')
    os.environ.setdefault('CUDA_AUTO_BOOST', '1')
    os.environ.setdefault('CUDA_MODULE_LOADING', 'LAZY')
    os.environ.setdefault('CUDA_DEVICE_DEFAULT_PERSISTING_L2_CACHE_PERCENTAGE_LIMIT', '0')
    os.environ.setdefault('GRADIO_ANALYTICS_ENABLED', 'False')
    os.environ.setdefault('SAFETENSORS_FAST_GPU', '1')
    os.environ.setdefault('NUMEXPR_MAX_THREADS', '16')
    os.environ.setdefault('PYTHONHTTPSVERIFY', '0')
    os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')   

def run_setup():
    set_environment()
    install_repositories()

if __name__ == "__main__":
    run_setup()

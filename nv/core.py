import json
import logging
import os
import re
import shutil
from os import mkdir, makedirs
from os.path import exists, join, basename, dirname, realpath, expanduser, expandvars

import boto3
import sh

from .crypto import DisabledCrypto, Crypto, keyring_store, keyring_retrieve

logger = logging.getLogger(__name__)

workon_home = realpath(expanduser(expandvars(os.environ.get('WORKON_HOME') or '~/.virtualenvs')))


def create(project_dir, environment_name='', project_name=None, use_pew=False, aws_profile=None,
           environment_vars=None, password=None, use_keyring=False, python_virtualenv=None, python_bin=None):
    project_dir = realpath(project_dir)
    _valid_environment_name(environment_name)
    nv_dir = join(project_dir, _folder_name(environment_name))
    if exists(nv_dir):
        raise RuntimeError("Environment already exists at '{0}'".format(nv_dir))

    if environment_vars:
        if not isinstance(environment_vars, dict):
            raise RuntimeError('Environment: Expected dict got {0}'.format(type(environment_vars)))
        for k, v in environment_vars.items():
            if not isinstance(v, str):
                raise RuntimeError('Environment "{0}" expected str got {1}'.format(k, type(v)))

    if not project_name:
        project_name = basename(project_dir)

    if password:
        crypto = Crypto.from_password(password)
        if use_keyring:
            keyring_store(nv_dir, password)
    else:
        crypto = DisabledCrypto()

    nv_conf = {
        'project_name': project_name,
        'environment_name': environment_name,
        'aws_profile': aws_profile,
        'encryption': crypto.get_memo(),
    }
    # Fallback for `use_pew`
    if python_virtualenv is None:
        python_virtualenv = use_pew
    if python_bin or python_virtualenv:
        if environment_name:
            venv = "{0}-{1}".format(project_name, environment_name)
        else:
            venv = project_name
        venv = "{}-{}".format(venv, os.urandom(4).hex())  # prevent name collisions
        logger.info('Setting up a virtual environment... ({0})'.format(venv))
        if not exists(workon_home):
            makedirs(workon_home)
        if python_bin:
            sh.virtualenv('--python', python_bin, join(workon_home, venv), _cwd=workon_home, _fg=True)
        else:
            sh.virtualenv(join(workon_home, venv), _cwd=workon_home, _fg=True)
        nv_conf.update({
            'venv': venv
        })

    mkdir(nv_dir)
    with open(join(nv_dir, 'nv.json'), 'w') as fp:
        json.dump(nv_conf, fp, indent=2)

    if environment_vars:
        with open(join(nv_dir, 'environment.json'), 'w') as fp:
            crypto.json_dump(fp, environment_vars)
    return nv_dir


def remove(project_dir, environment_name=''):
    nv_dir, nv_conf = _load_nv(project_dir, environment_name)
    venv = nv_conf.get('venv')
    if venv:
        shutil.rmtree(join(workon_home, venv))
    shutil.rmtree(nv_dir)


def launch_shell(project_dir, environment_name='', password=None, update_keyring=False):
    return invoke(
        command=os.environ['SHELL'], arguments=[],
        project_dir=project_dir, environment_name=environment_name,
        password=password, update_keyring=update_keyring
    )


def invoke(command, arguments, project_dir, environment_name='', password=None, update_keyring=False):
    new_env = _prepare_environment(
        project_dir=project_dir, environment_name=environment_name,
        password=password, update_keyring=update_keyring
    )
    search_paths = new_env.get('PATH', '').split(os.pathsep)
    try:
        cmd = sh.Command(command, search_paths)
        cmd = [cmd._path]
        cmd += arguments
        os.execve(cmd[0], cmd, new_env)
        raise Exception('Unreachable')
    except sh.CommandNotFound:
        raise RuntimeError('executable not found: {}'.format(command))



def _prepare_environment(project_dir, environment_name='', password=None, update_keyring=False):
    nv_dir, nv_conf = _load_nv(project_dir, environment_name)
    if password and update_keyring:
        keyring_store(nv_dir, password)
    elif not password:
        password = keyring_retrieve(nv_dir)

    if password:
        crypto = Crypto.from_memo(nv_conf.get('encryption'), password)
    else:
        crypto = DisabledCrypto()

    # TODO Unset environment variables based on pattern.
    new_env = os.environ.copy()
    path_prepends = []
    new_env.update({
        'NV_PROJECT': nv_conf['project_name'],
        'NV_PROJECT_DIR': dirname(nv_dir),
        'NV_ENVIRONMENT': nv_conf['environment_name'],
        'NV_ENVIRONMENT_DIR': nv_dir,
    })
    venv = nv_conf.get('venv', nv_conf.get('pew'))
    if venv:
        venv_dir = join(workon_home, venv)
        new_env.pop('PYTHONHOME', None)
        new_env.pop('__PYVENV_LAUNCHER__', None)
        path_prepends.append(join(venv_dir, 'bin'))
        new_env.update({
            'VIRTUAL_ENV': venv_dir,
        })
    aws_profile = nv_conf.get('aws_profile')
    if aws_profile:
        session = boto3.Session(profile_name=aws_profile)
        creds = session.get_credentials().get_frozen_credentials()
        # TODO Add notice re- expiry of credentials
        new_env.update({
            'AWS_DEFAULT_REGION': session.region_name,
            'AWS_ACCESS_KEY_ID': creds.access_key,
            'AWS_SECRET_ACCESS_KEY': creds.secret_key,
            'AWS_SESSION_TOKEN': creds.token or '',
        })

    if exists(join(nv_dir, 'environment.json')):
        with open(join(nv_dir, 'environment.json'), 'r') as fp:
            extra_env = crypto.json_load(fp)
        if not isinstance(extra_env, dict):
            raise RuntimeError('Environment: Expected dict got {0}'.format(type(extra_env)))
        for k, v in extra_env.items():
            if not isinstance(v, str):
                raise RuntimeError('Environment "{0}" expected str got {1}'.format(k, type(v)))
        new_env.update(extra_env)

    if path_prepends:
        new_env.update({
            'PATH': os.pathsep.join(path_prepends + [new_env['PATH'],])
        })
    return new_env


def _valid_environment_name(environment_name):
    if not isinstance(environment_name, str):
        raise TypeError('Expected string got: {0}'.format(type(environment_name)))

    if not environment_name or re.match(r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$', environment_name):
        return environment_name
    raise ValueError()


def _folder_name(environment_name=''):
    if environment_name:
        return '.nv-{}'.format(environment_name)
    else:
        return '.nv'


def _load_nv(project_dir, environment_name):
    project_dir = realpath(project_dir)
    _valid_environment_name(environment_name)
    nv_dir = join(project_dir, _folder_name(environment_name))
    if not exists(nv_dir):
        raise RuntimeError("Not found: '{0}'".format(nv_dir))
    with open(join(nv_dir, 'nv.json'), 'r') as fp:
        nv_conf = json.load(fp)
    return nv_dir, nv_conf

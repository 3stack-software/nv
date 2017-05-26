from __future__ import absolute_import, division, print_function, unicode_literals

import json
import logging
import os
import re
import shutil
from os import mkdir
from os.path import exists, join, basename, dirname, realpath

import boto3
import sh
import six

from .crypto import DisabledCrypto, Crypto, keyring_store, keyring_retrieve

logger = logging.getLogger(__name__)


def create(project_dir, environment_name='', project_name=None, use_pew=False, aws_profile=None,
           environment_vars=None, password=None, use_keyring=False):
    project_dir = realpath(project_dir)
    _valid_environment_name(environment_name)
    nv_dir = join(project_dir, _folder_name(environment_name))
    if exists(nv_dir):
        raise RuntimeError("Environment already exists at '{0}'".format(nv_dir))

    if environment_vars:
        if not isinstance(environment_vars, dict):
            raise RuntimeError('Environment: Expected dict got {0}'.format(type(environment_vars)))
        for k, v in environment_vars.items():
            if not isinstance(v, six.string_types):
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

    if use_pew:
        if environment_name:
            pew_env = "{0}-{1}".format(project_name, environment_name)
        else:
            pew_env = project_name
        logger.info('Setting up a virtual environment... ({0})'.format(pew_env))
        # "-d" flag causes environment _not_ to activate when created
        sh.pew('new', '-d', '-a', project_dir, pew_env, _fg=True)
        nv_conf.update({
            'pew': pew_env
        })

    mkdir(nv_dir)
    with open(join(nv_dir, 'nv.json'), 'wb') as fp:
        json.dump(nv_conf, fp, indent=2)

    if environment_vars:
        with open(join(nv_dir, 'environment.json'), 'wb') as fp:
            crypto.json_dump(fp, environment_vars)
    return nv_dir


def remove(project_dir, environment_name=''):
    nv_dir, nv_conf = _load_nv(project_dir, environment_name)
    pew_env = nv_conf.get('pew')
    if pew_env:
        try:
            sh.pew.rm(pew_env, _fg=True)
        except sh.ErrorReturnCode:
            pass
    shutil.rmtree(nv_dir)


def launch_shell(project_dir, environment_name='', password=None, update_keyring=False):
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
    new_env.update({
        'NV_PROJECT': nv_conf['project_name'],
        'NV_PROJECT_DIR': dirname(nv_dir),
        'NV_ENVIRONMENT': nv_conf['environment_name'],
        'NV_ENVIRONMENT_DIR': nv_dir,
    })
    if 'PS1' in os.environ:
        if nv_conf['environment_name']:
            nickname = '{0[project_name]}:{0[environment_name]}'.format(nv_conf)
        else:
            nickname = '{0[project_name]}'.format(nv_conf)
        new_env.update({
            # specify non-printing sequences (e.g. color codes) as non-printing, using \[...\]
            'PS1': r'\[\e[01m\]{nickname}\[\e[0m\] {ps1}'.format(nickname=nickname, ps1=os.environ['PS1']),
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
        with open(join(nv_dir, 'environment.json'), 'rb') as fp:
            extra_env = crypto.json_load(fp)
        if not isinstance(extra_env, dict):
            raise RuntimeError('Environment: Expected dict got {0}'.format(type(extra_env)))
        for k, v in extra_env.items():
            if not isinstance(v, six.text_type):
                raise RuntimeError('Environment "{0}" expected str got {1}'.format(k, type(v)))
        new_env.update(extra_env)

    pew_env = nv_conf.get('pew')
    try:
        if pew_env:
            sh.pew.workon(pew_env, _env=new_env, _fg=True)
        else:
            # TODO seems too simple, are we missing anything
            sh.Command(os.environ['SHELL'])(_fg=True, _env=new_env)
    except sh.ErrorReturnCode:
        pass


def _valid_environment_name(environment_name):
    if not isinstance(environment_name, six.string_types):
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
    with open(join(nv_dir, 'nv.json'), 'rb') as fp:
        nv_conf = json.load(fp)
    return nv_dir, nv_conf

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import logging
import os
import shutil
from os import mkdir
from os.path import exists, join, basename

import boto3
import sh

logger = logging.getLogger(__name__)


def create(environment_name, project_dir, project_name=None, use_pew=False, aws_profile=None):
    # TODO check that environment_name contains only [a-z0-9_]
    # TODO check that project_dir is fully resolved

    nv_dir = join(project_dir, '.nv-{0}'.format(environment_name))
    if exists(nv_dir):
        raise RuntimeError("Environment exists at '{0}'".format(nv_dir))

    if not project_name:
        project_name = basename(project_dir)

    nv_conf = {
        'project_name': project_name,
        'environment_name': environment_name,
        'aws_profile': aws_profile,
    }

    if use_pew:
        pew_env = "{0}-{1}".format(project_name, environment_name)
        logger.info('Setting up a virtual environment... ({0})'.format(pew_env))
        # "-d" flag causes environment _not_ to activate when created
        sh.pew('new', '-d', '-a', project_dir, pew_env, _fg=True)
        nv_conf.update({
            'pew': pew_env
        })

    mkdir(nv_dir)
    with open(join(nv_dir, 'nv.json'), 'wb') as fp:
        json.dump(nv_conf, fp, indent=2)

    return nv_dir


def remove(environment_name, project_dir):
    nv_dir = join(project_dir, '.nv-{0}'.format(environment_name))
    if not exists(nv_dir):
        raise RuntimeError("Not found: '{0}'".format(nv_dir))
    with open(join(nv_dir, 'nv.json'), 'rb') as fp:
        nv_conf = json.load(fp)
    pew_env = nv_conf.get('pew')
    if pew_env:
        try:
            sh.pew.rm(pew_env, _fg=True)
        except sh.ErrorReturnCode:
            pass
    shutil.rmtree(nv_dir)


def launch_shell(environment_name, project_dir):
    nv_dir = join(project_dir, '.nv-{0}'.format(environment_name))
    if not exists(nv_dir):
        raise RuntimeError("Not found: '{0}'".format(nv_dir))
    with open(join(nv_dir, 'nv.json'), 'rb') as fp:
        nv_conf = json.load(fp)

    # TODO Unset environment variables based on pattern.
    new_env = os.environ.copy()
    new_env.update({
        'NV_PROJECT': nv_conf['project_name'],
        'NV_PROJECT_DIR': project_dir,
        'NV_ENVIRONMENT': nv_conf['environment_name'],
        'NV_ENVIRONMENT_DIR': nv_dir,
        'PS1': r'\[\e[01m{0[project_name]}:{0[environment_name]}\e[0m\] {1}'.format(nv_conf, os.environ['PS1']),
    })
    aws_profile = nv_conf.get('aws_profile')
    if aws_profile:
        session = boto3.Session(profile_name=aws_profile)
        creds = session.get_credentials().get_frozen_credentials()
        # TODO Add notice re- expiry of credentials
        new_env.update({
            'AWS_ACCESS_KEY_ID': creds.access_key,
            'AWS_SECRET_ACCESS_KEY': creds.secret_key,
            'AWS_SESSION_TOKEN': creds.token,
        })

    if exists(join(nv_dir, 'environment.json')):
        with open(join(nv_dir, 'environment.json'), 'rb') as fp:
            extra_env = json.load(fp)
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


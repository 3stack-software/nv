import logging
import os

import click

from .core import create, remove, launch_shell, _valid_environment_name

logging.basicConfig()
logger = logging.getLogger(__name__)


@click.group()
def main():
    pass


@main.command('create')
@click.argument('environment_name', default='', type=_valid_environment_name)
@click.option('--project-name', '-p', default=None,
              help='''Your project name (defaults to current directory name)''')
@click.option('--project-dir', '-d', default='.',
              type=click.Path(file_okay=False, dir_okay=True, exists=True),
              help='''Path to the project project (defaults to current directory)''')
@click.option('use_pew', '--pew', is_flag=True, default=False,
              help='''Activate a python virtualenv via pew''')
@click.option('--aws-profile', default=None,
              help='''Obtain credentials for the given profile.''')
@click.option('environment_vars', '--env', type=(unicode, unicode), multiple=True)
@click.option('wants_password', '-P', default=False, is_flag=True)
@click.option('use_keyring', '-K', default=False, is_flag=True)
def cmd_create(environment_name, project_name, project_dir, use_pew, aws_profile, environment_vars, wants_password, use_keyring):
    """Create a new environment in %PROJECT%/.nv-%ENVIRONMENT_NAME%"""
    password = None
    if wants_password:
        password = click.prompt('Password', hide_input=True)

    nv_dir = create(project_dir, environment_name, project_name=project_name, use_pew=use_pew, aws_profile=aws_profile,
                    environment_vars=dict(environment_vars), password=password, use_keyring=use_keyring)
    rel_dir = os.path.relpath(nv_dir, os.getcwd())
    click.echo("""
environment created at {0}.
Launch with:
\tnv shell {1}

Specify extra environment variables by editing {0}/environment.json
    """.format(rel_dir, environment_name))


@main.command('rm')
@click.argument('environment_name', default='', type=_valid_environment_name)
@click.option('--project-dir', '-d', default='.',
              type=click.Path(file_okay=False, dir_okay=True, exists=True),
              help='''Path to the project project (defaults to current directory)''')
def cmd_remove(environment_name, project_dir):
    """Remove an environment."""
    click.echo("Removing {0} in {1}".format(environment_name, project_dir))
    remove(project_dir, environment_name)


@main.command('shell')
@click.argument('environment_name', default='', type=_valid_environment_name)
@click.option('--project-dir', '-d', default='.',
              type=click.Path(file_okay=False, dir_okay=True, exists=True),
              help='''Path to the project project (defaults to current directory)''')
@click.option('wants_password', '-P', default=False, is_flag=True)
@click.option('update_keyring', '-K', default=False, is_flag=True)
def cmd_shell(environment_name, project_dir, wants_password, update_keyring):
    """Launch a new shell in the specified environment."""
    click.echo("Launching nv subshell. Type 'exit' or 'Ctrl+D' to return.")
    password = None
    if wants_password:
        password = click.prompt('Password', hide_input=True)

    launch_shell(project_dir, environment_name, password, update_keyring)
    click.echo('Environment closed.')

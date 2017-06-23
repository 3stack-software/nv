import logging
import os

import click

from .core import create, remove, launch_shell, invoke, _valid_environment_name

logging.basicConfig()
logger = logging.getLogger(__name__)


@click.group()
@click.option('--environment-name', '-n', default='', type=_valid_environment_name)
@click.option('--project-dir', '-d', default='.',
              type=click.Path(file_okay=False, dir_okay=True, exists=True),
              help='''Path to the project project (defaults to current directory)''')
@click.option('wants_password', '-P', default=False, is_flag=True)
@click.option('use_keyring', '-K', default=False, is_flag=True)
@click.pass_context
def main(ctx, environment_name, project_dir, wants_password, use_keyring):
    password = None
    if wants_password:
        password = click.prompt('Password', hide_input=True)
    ctx.obj = (environment_name, project_dir, password, use_keyring)


@main.command('create')
@click.option('--project-name', '-p', default=None,
              help='''Your project name (defaults to current directory name)''')
@click.option('--python-virtualenv', '-py', is_flag=True, default=False,
              help='''Activate a python virtualenv''')
@click.option('--aws-profile', default=None,
              help='''Obtain credentials for the given profile.''')
@click.option('environment_vars', '--env', type=(unicode, unicode), multiple=True,
              help='''Name & Value of environment variables to set''')
@click.pass_context
def cmd_create(ctx, project_name, python_virtualenv, aws_profile, environment_vars):
    """Create a new environment in %PROJECT%/.nv-%ENVIRONMENT_NAME%"""
    environment_name, project_dir, password, use_keyring = ctx.obj
    nv_dir = create(
        project_dir, environment_name, project_name=project_name, python_virtualenv=python_virtualenv,
        aws_profile=aws_profile, environment_vars=dict(environment_vars), password=password, use_keyring=use_keyring
    )
    rel_dir = os.path.relpath(nv_dir, os.getcwd())
    click.echo("""
environment created at "{0}"
Launch with:
\tnv shell {1}

Specify extra environment variables by editing {0}/environment.json
    """.format(rel_dir, environment_name))


@main.command('rm')
@click.pass_context
def cmd_remove(ctx):
    """Remove an environment."""
    environment_name, project_dir = ctx.obj[:2]
    click.echo("Removing {0} in {1}".format(environment_name, project_dir))
    remove(project_dir, environment_name)


@main.command('shell')
@click.pass_context
def cmd_shell(ctx):
    """Launch a new shell in the specified environment."""
    environment_name, project_dir, password, use_keyring = ctx.obj
    click.echo("Launching nv subshell. Type 'exit' or 'Ctrl+D' to return.")
    exit_code = launch_shell(project_dir, environment_name, password, use_keyring)
    click.echo('Environment closed.')
    if exit_code:
        raise ExitCode('Non-zero exit', exit_code)


@main.command('run', context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True
))
@click.argument('command')
@click.argument('args', nargs=-1)
@click.pass_context
def cmd_run(ctx, command, args):
    """Runs a command in the specified environment."""
    environment_name, project_dir, password, use_keyring = ctx.obj
    exit_code = invoke(command, args, project_dir, environment_name, password, use_keyring)
    if exit_code:
        raise ExitCode('Non-zero exit', exit_code)


class ExitCode(click.ClickException):
    def __init__(self, message, exit_code):
        self.exit_code = exit_code
        super(ExitCode, self).__init__(message)

    def show(self, file=None):
        pass

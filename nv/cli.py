import click

import logging
import os
from .core import create, remove, launch_shell

logging.basicConfig()
logger = logging.getLogger(__name__)


@click.group()
def main():
    pass


@main.command('create')
@click.argument('environment_name', default='dev')
@click.option('--project-name', '-p', default=None,
              help='''Your project name (defaults to current directory name)''')
@click.option('--project-dir', '-d', default='.',
              type=click.Path(file_okay=False, dir_okay=True, exists=True, resolve_path=True),
              help='''Path to the project project (defaults to current directory)''')
@click.option('use_pew', '--pew', is_flag=True, default=False,
              help='''Activate a python virtualenv via pew''')
@click.option('--aws-profile', default=None,
              help='''Obtain credentials for the given profile.''')
@click.pass_context
def cmd_nv_create(ctx, environment_name, project_name, project_dir, use_pew, aws_profile):
    """Create a new environment in %PROJECT%/.nv-%ENVIRONMENT_NAME%"""
    nv_dir = create(environment_name, project_dir, project_name=project_name, use_pew=use_pew, aws_profile=aws_profile)
    rel_dir = os.path.relpath(nv_dir, os.getcwd())
    click.echo("""
environment created at {0}.
Launch with:
\tnv shell {1}

Specify extra environment variables by editing {0}/environment.json
    """.format(rel_dir, environment_name))


@main.command('rm')
@click.argument('environment_name', default='dev')
@click.option('--project-dir', '-d', default='.',
              type=click.Path(file_okay=False, dir_okay=True, exists=True, resolve_path=True),
              help='''Path to the project project (defaults to current directory)''')
def cmd_remove(environment_name, project_dir):
    """Remove an environment."""
    click.echo("Removing {0} in {1}".format(environment_name, project_dir))
    remove(environment_name, project_dir)


@main.command('shell')
@click.argument('environment_name', default='dev')
@click.option('--project-dir', '-d', default='.',
              type=click.Path(file_okay=False, dir_okay=True, exists=True, resolve_path=True),
              help='''Path to the project project (defaults to current directory)''')
def cmd_shell(environment_name, project_dir):
    """Launch a new shell in the specified environment."""
    click.echo("Launching nv subshell. Type 'exit' or 'Ctrl+D' to return.")
    launch_shell(environment_name, project_dir)
    click.echo('Environment closed.')

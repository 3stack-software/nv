import click

import logging
from .core import create, remove, launch_shell

logging.basicConfig()
logger = logging.getLogger(__name__)


@click.group()
def main():
    pass


@main.command('create')
@click.argument('environment_name')
@click.option('--project-name', '-p', default=None)
@click.option('--project-dir', '-d', default='.', type=click.Path(file_okay=False, dir_okay=True, exists=True, resolve_path=True))
@click.option('use_pew', '--pew', is_flag=True, default=False)
@click.option('--aws-profile', default=None, help='''Obtain temporary credentials.''')
@click.pass_context
def cmd_nv_create(ctx, environment_name, project_name, project_dir, use_pew, aws_profile):
    """Create a new environment (in the current directory)."""
    nv_dir = create(environment_name, project_dir, project_name=project_name, use_pew=use_pew, aws_profile=aws_profile)
    click.echo("""
e|nv|ironment created at {0}.
Launch with:
\tnv shell {1}
    """.format(nv_dir, environment_name))


@main.command('rm')
@click.argument('environment_name')
@click.option('--project-dir', '-d', default='.', type=click.Path(file_okay=False, dir_okay=True, exists=True, resolve_path=True))
def cmd_remove(environment_name, project_dir):
    """Remove an environment."""
    click.echo("Removing {0} in {1}".format(environment_name, project_dir))
    remove(environment_name, project_dir)


@main.command('shell')
@click.argument('environment_name')
@click.option('--project-dir', '-d', default='.', type=click.Path(file_okay=False, dir_okay=True, exists=True, resolve_path=True))
def cmd_shell(environment_name, project_dir):
    """Launch a new shell in the specified environment."""
    click.echo("Launching nv subshell. Type 'exit' or 'Ctrl+D' to return.")
    launch_shell(environment_name, project_dir)
    click.echo('Environment closed.')

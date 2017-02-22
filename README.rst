nv (environment manager)
========================

A tool to help users manage multiple environments.

When launching a shell in the environment, it sets sets
environment variables automatically.

It can also integrate with Python Virtual Environments,
AWS Profiles (eg. Assume Role).

Once you've created an environment, edit the environment.json
to configure additional environment variables.

Usage
-----

::

    $ nv
    Usage: nv [OPTIONS] COMMAND [ARGS]...

    Options:
      --help  Show this message and exit.

    Commands:
      create  Create a new environment (in the current...
      rm      Remove an environment.
      shell   Launch a new shell in the specified...

::

    $ nv create --help

    Usage: nv create [OPTIONS] [ENVIRONMENT_NAME]

      Create a new environment in %PROJECT%/.nv-%ENVIRONMENT_NAME%

    Options:
      -p, --project-name TEXT      Your project name (defaults to current
                                   directory name)
      -d, --project-dir DIRECTORY  Path to the project project (defaults to
                                   current directory)
      --pew                        Activate a python virtualenv via pew
      --aws-profile TEXT           Obtain credentials for the given profile.
      --help                       Show this message and exit.


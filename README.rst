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
      -n, --environment-name _VALID_ENVIRONMENT_NAME
      -d, --project-dir DIRECTORY     Path to the project project (defaults to
                                      current directory)
      -P
      -K
      --help                          Show this message and exit.

    Commands:
      create  Create a new environment in...
      rm      Remove an environment.
      run     Runs a command in the specified environment.
      shell   Launch a new shell in the specified...

::

    $ nv create --help

    Usage: nv create [OPTIONS]

      Create a new environment in %PROJECT%/.nv-%ENVIRONMENT_NAME%

    Options:
      -p, --project-name TEXT   Your project name (defaults to current directory
                                name)
      -py, --python-virtualenv  Activate a python virtualenv
      --aws-profile TEXT        Obtain credentials for the given profile.
      --env <TEXT TEXT>...      Name & Value of environment variables to set
      --help                    Show this message and exit.

::

    $ nv shell --help

    Usage: nv shell [OPTIONS]

      Launch a new shell in the specified environment.

    Options:
      --help  Show this message and exit.

::

    $ nv run --help

    Usage: nv run [OPTIONS] COMMAND [ARGS]...

      Runs a command in the specified environment.

    Options:
      --help  Show this message and exit.


__version__ = __import__('pkg_resources').resource_string(__name__, 'VERSION')

from .core import create, remove, launch_shell

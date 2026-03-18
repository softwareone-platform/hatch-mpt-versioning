from hatchling.plugin import hookimpl

from .version_source import MptGitDescribeVersionSource


@hookimpl
def hatch_register_version_source():
    return MptGitDescribeVersionSource


"""Synapse Annotation Platform"""

import importlib.metadata

# Package name
package_name = "synapse"

# Package version
try:
    __version__ = importlib.metadata.metadata(package_name).get("version")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0.dev"

# pypi info
__latest_version__ = None
__current_version_is_outdated__ = False
__latest_version_upload_time__ = None
__latest_version_check_time__ = None






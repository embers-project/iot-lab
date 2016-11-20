# pylint: disable=import-error,no-name-in-module
# pylint: disable=wrong-import-order
try:  # pragma: no cover
    from urllib.error import HTTPError
except ImportError:  # pragma: no cover
    # pylint: disable=import-error,no-name-in-module
    from urllib2 import HTTPError

import abc
import typing
import hashlib
from core import utils


class BaseMetadata(metaclass=abc.ABCMeta):
    """The BaseMetadata object provides the base structure for all metadata returned via
    WaterButler.  It also implements the API serialization methods to turn metadata objects
    into primitive data structures suitable for serializing.

    The basic metadata response looks like::

        {
          "path": "",
          "name": "",
          "kind": "",
          "provider": "",
          "materialized": "",
          "provider": "",
          "etag": "",
          "extra": {}
        }
    """

    def __init__(self, raw: dict) -> None:
        self.raw = raw

    def serialized(self) -> dict:
        """Returns a dict of primitives suitable for serializing into JSON.

        .. note::

            This method determines the output of API v0 and v1.

        :rtype: dict
        """
        return {
            'kind': self.kind,
            'name': self.name,
            'path': self.path,
            'provider': self.provider,
            'materialized': self.materialized_path,
            'etag': hashlib.sha256('{}::{}'.format(self.provider, self.etag).encode('utf-8')).hexdigest(),
        }

    def build_path(self, path) -> str:
        if not path.startswith('/'):
            path = '/' + path
        if self.kind == 'folder' and not path.endswith('/'):
            path += '/'
        return path

    @property
    def is_folder(self) -> bool:
        """ Does this object describe a folder?

        :rtype: bool
        """
        return self.kind == 'folder'

    @property
    def is_file(self) -> bool:
        """ Does this object describe a file?

        :rtype: bool
        """
        return self.kind == 'file'

    @property
    @abc.abstractmethod
    def provider(self) -> str:
        """ The provider from which this resource originated. """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def kind(self) -> str:
        """ `file` or `folder` """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """ The user-facing name of the entity, excluding parent folder(s).
        ::

            /bar/foo.txt -> foo.txt
            /<someid> -> whatever.png
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def path(self) -> str:
        """ The canonical string representation of a waterbutler file or folder.  For providers
        that track entities with unique IDs, this will be the ID.  For providers that do not, this
        will usually be the full unix-style path of the file or folder.

        .. note::

            All paths MUST start with a `/`
            All folder entities MUST end with a `/`
            File entities MUST never end with a `/`
        """
        raise NotImplementedError

    @property
    def materialized_path(self) -> str:
        """ The unix-style path of the file relative the the root of the provider.  Encoded
        entities should be decoded.

        e.g.::

            path              -> /313c57f9a9edeb87139b205beaed
            name              -> Foo.txt
            materialized_path -> /Parent Folder/Foo.txt

        .. note::

            All materialized_paths MUST start with a `/`
            All folder entities MUST end with a `/`
            File entities MUST never end with a `/`

        .. note::

            Defaults to `self.path`
        """
        return self.path


class BaseFileMetadata(BaseMetadata):
    """ The base class for WaterButler metadata objects for files.  In addition to the properties
    required by `BaseMetadata`, `BaseFileMetadata` requires the consumer to implement the
    `content_type`, `modified`, and `size` properties.  The `etag` may be added in a subclass.
    """

    def serialized(self) -> dict:
        """ Returns a dict representing the file's metadata suitable to be serialized into JSON.

        :rtype: dict
        """
        return dict(super().serialized(), **{
            'contentType': self.content_type,
            'modified': self.modified,
            'modified_utc': self.modified_utc,
            'created_utc': self.created_utc,
            'size': self.size,
            'sizeInt': self.size_as_int,
        })


    @property
    def kind(self) -> str:
        """ File objects have `kind == 'file'` """
        return 'file'

    @property
    @abc.abstractmethod
    def content_type(self) -> str:
        """ MIME-type of the file (if available) """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def modified(self) -> str:
        """ Date the file was last modified, as reported by the provider, in
        the format used by the provider. """
        raise NotImplementedError

    @property
    def modified_utc(self) -> str:
        """ Date the file was last modified, as reported by the provider,
        converted to UTC, in format (YYYY-MM-DDTHH:MM:SS+00:00). """
        return utils.normalize_datetime(self.modified)


    @property
    @abc.abstractmethod
    def size(self) -> typing.Union[int, str]:
        """ Size of the file in bytes. Should be a int, but some providers return a string and WB
        never casted it.  The `size_as_int` property was added to enforce this without breaking
        exisiting code and workarounds.
        """
        raise NotImplementedError

    @property
    def size_as_int(self) -> int:
        """ Size of the file in bytes.  Always an `int` or `None`. Some providers report size as a
        `str`. Both exist to maintain backwards compatibility.
        """
        try:
            size_as_int = int(self.size)
        except (TypeError, ValueError):
            size_as_int = None
        return size_as_int


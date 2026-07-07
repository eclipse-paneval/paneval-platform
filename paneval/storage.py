import abc
import os
from typing import IO, BinaryIO, Optional, Union, Dict, Any

from django.conf import settings


class ObjectStorage(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_conf(self) -> Dict[str, Any]:
        pass

    @abc.abstractmethod
    def get_key(self, key: str) -> Optional[BinaryIO]:
        pass

    @abc.abstractmethod
    def upload(self, key: str, fobj: Union[IO, str, bytes]) -> str:
        pass

    @abc.abstractmethod
    def head_key_length(self, key: str) -> int:
        pass

    @abc.abstractmethod
    def full_uri(self, key: str) -> str:
        pass


class FilesystemObjectStorage(ObjectStorage):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def full_uri(self, key: str) -> str:
        return self._resolve(key)

    def _resolve(self, key: str) -> str:
        return os.path.join(self.base_dir, key)

    def get_conf(self) -> Dict[str, Any]:
        return {
            'storage': 'filesystem',
            'base_dir': self.base_dir,
        }

    def get_key(self, key: str) -> Optional[BinaryIO]:
        path = self._resolve(key)
        if not os.path.isfile(path):
            return None
        return open(path, "rb")

    def upload(self, key: str, fobj: Union[IO, str, bytes]) -> str:
        path = self._resolve(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if isinstance(fobj, bytes):
            data = fobj
        elif isinstance(fobj, str):
            data = fobj.encode()
        else:
            data = fobj.read()
        with open(path, "wb") as f:
            f.write(data)
        return key

    def head_key_length(self, key: str) -> int:
        path = self._resolve(key)
        return os.path.getsize(path)


store: ObjectStorage = FilesystemObjectStorage(settings.FILESYSTEM_OBJECT_STORAGE_PATH)

import os
import pathlib
from configparser import ConfigParser


class ConfParser:

    def __init__(self, path: str | pathlib.Path, conf_file_name: str = 'locations.ini') -> None:
        assert isinstance(conf_file_name, str) and conf_file_name.endswith('.ini')
        self._path = path
        self._conf_file_name = conf_file_name
        self._parser = ConfigParser()
        self._parsed = False

    def _read(self, file_path: pathlib.Path) -> None:
        self._parser.read(file_path)
        self._parsed = True

    def _get_file(self):
        for *_, filenames in os.walk(self._path):
            if self._conf_file_name in filenames:
                return self._path / self._conf_file_name

    def parse(self) -> ConfigParser:
        if not self._parsed:
            if (file := self._get_file()) is None:
                raise FileNotFoundError(f"file {self._conf_file_name} not found")
            self._read(file)

        return self._parser

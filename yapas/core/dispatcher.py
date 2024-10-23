from yapas.conf.parser import ConfParser
from yapas.core.abs.dispatcher import AbstractDispatcher
from yapas.core.server import handlers

_HANDLER_MAPPING = {
    'proxy': handlers.proxy,
    'proxy_static': handlers.proxy_static,
    'server_static': handlers.server_static,
    'restart': handlers.restart,
    'metrics': handlers.metrics,
    'router': handlers.index,  # todo переделать под обработку роутером
}


class ProxyDispatcher(AbstractDispatcher):

    @classmethod
    def from_conf(cls, conf: ConfParser) -> "ProxyDispatcher":
        """Create a Dispatcher instance from a configuration file."""
        settings = conf.parse()
        obj = cls()

        locations = {}
        for section in settings.sections():
            if not section.startswith('locations'):
                continue

            _, name = section.split(':')
            locations[name] = None  # for now

            loc_info = settings[section]
            regex = loc_info.get('regex')
            type_ = loc_info.get('type')

            try:
                obj.add_location(regex, _HANDLER_MAPPING[type_])
            except KeyError:
                raise ValueError(f'only {", ".join(_HANDLER_MAPPING.keys())} locations are supported')

        return obj

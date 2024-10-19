from logging.config import dictConfig


def setup_logging(level: str) -> None:
    """Setup logging for the app"""
    dictConfig({
        'version': 1,
        'disable_existing_loggers': False,

        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': level,
                'formatter': 'detailed',
                'stream': 'ext://sys.stderr',
            },
        },

        'formatters': {
            'detailed': {
                'format': '[%(asctime)s] %(levelname)-7s %(name)s:%(lineno)s - %(message)s',
            },
        },

        'loggers': {
            '': {
                'level': level,
                'handlers': [
                    'console',
                ],
            },
        },
    })

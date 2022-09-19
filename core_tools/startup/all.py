import logging
import os
from datetime import datetime

from core_tools.GUI.qt_util import qt_init
from .config import load_configuration
from .db_connection import (
        connect_local_db,
        connect_remote_db,
        connect_local_and_remote_db)
from .sample_info import set_sample_info


def configure(filename):
    qt_init()
    cfg = load_configuration(filename)
    _configure_logging(cfg)
    _configure_sample(cfg)
    _connect_to_db(cfg)


def _configure_sample(cfg):
    project = cfg['project']
    setup = cfg['setup']
    sample = cfg['sample']
    set_sample_info(project, setup, sample)


def _connect_to_db(cfg):
    use_local = cfg.get('local_database') is not None
    use_remote = cfg.get('remote_database') is not None

    if use_local and use_remote:
        connect_local_and_remote_db()
    elif use_local:
        connect_local_db()
    elif use_remote:
        connect_remote_db()
    else:
        logging.warning('No database configured')


def _generate_log_file_name():
    pid = os.getpid()
    now = datetime.now()
    return f"{now:%Y-%m-%d}({pid:06d}).log"


def _configure_logging(cfg):
    path = cfg.get('logging.file_location', '~/.core_tools')
    file_level = cfg.get('logging.file_level', 'INFO')
    console_level = cfg.get('logging.console_level', 'WARNING')
    logger_levels = cfg.get('logging.logger_levels', {})

    name = _generate_log_file_name()
    file_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    console_format = '%(name)-12s: %(levelname)-8s %(message)s'

    path = os.path.expanduser(path)
    os.makedirs(path, exist_ok=True)
    filename = os.path.join(path, name)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    for handler in root_logger.handlers:
        handler.close()
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(logging.Formatter(console_format))
    root_logger.addHandler(console_handler)

    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename, when="midnight", encoding="utf-8"
    )

    file_handler.setLevel(file_level)
    file_handler.setFormatter(logging.Formatter(file_format))
    root_logger.addHandler(file_handler)

    logging.info('Start logging')

    for name,level in logger_levels.items():
        logging.getLogger(name).setLevel(level)

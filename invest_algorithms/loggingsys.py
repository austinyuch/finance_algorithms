#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
from logging.handlers import TimedRotatingFileHandler

from confs import PATH_LOG_FOLDER, GLOBAL_LOG_LEVEL, LOG_BACKUP_COUNT


def generate_general_my_log(log_name=None, log_level=None, interval="m"):
    if log_name is None:
        log_name = __name__
    if interval == "d":
        logtimestr = time.strftime("%Y%m%d")  # daily log
    elif interval == "m":
        logtimestr = time.strftime("%Y%m")  # monthly log
    else:
        logtimestr = time.strftime("%Y")  # yearly log
    logfile_name = f'{log_name}_{logtimestr}.log'
    PATH_LOG_FOLDER.mkdir(parents=True, exist_ok=True)
    PATH_LOGFILE = PATH_LOG_FOLDER.joinpath(logfile_name)

    return MyLog(log_file_path=PATH_LOGFILE, log_name=log_name, log_level=log_level)


class MyLog():
    # TimedRotatingFileHandler: python 3.6+ supports Path object
    

    def __init__(self, log_file_path=None, log_name=None, log_level=None):
        # 如果沒有指定 log_name，會直接使用 MyLog 的 Module name (util.log) 做為 log_name
        # getLogger 沒有找到現存的 Log 時，就會使用 log_file_path 建立新的 log
        if log_name is None:
            self.log_name = __name__
        else:
            self.log_name = log_name

        self.logger = logging.getLogger(self.log_name)
        level_name = (log_level or GLOBAL_LOG_LEVEL or "INFO").upper()
        # logging.getLevelName(name) -> int for known names; fall back to INFO.
        self.logging_level = logging.getLevelName(level_name)
        if not isinstance(self.logging_level, int):
            self.logging_level = logging.INFO

        if not self.logger.handlers:
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            # CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET
            # logging.basicConfig(level=logging.WARNING, format='%(asctime)s|%(name)s|%(levelname)s|%(message)s')
            logging.basicConfig(level=self.logging_level, 
                                format='%(asctime)s|%(name)s|%(levelname)s|%(message)s',
                                datefmt="%Y-%m-%dT%H:%M:%S"
                            )
            int_backupCount = int(LOG_BACKUP_COUNT)
            th = TimedRotatingFileHandler(log_file_path, when="d", interval=1, backupCount=int_backupCount)
            # th.setLevel(logging.WARNING)
            th.setLevel(self.logging_level)
            th.setFormatter(formatter)
            self.logger.addHandler(th)
            
    def get_log_name(self):
        return self.log_name

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg, exc_info=True)

    def critical(self, msg):
        self.logger.critical(msg)

    def log(self, level, msg):
        self.logger.log(level, msg)

    def setLevel(self, level):
        self.logger.setLevel(level)

    def disable(self):
        logging.disable(50)

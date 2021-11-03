#**********************************************************************
# Copyright 2020 Advanced Micro Devices, Inc
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#********************************************************************
import sys
import logging
from logging import DEBUG, INFO, WARN, ERROR, CRITICAL

from . import PLUGIN_ROOT_DIR
from .. import config


FORMAT_STR = "%(asctime)s %(levelname)s %(name)s [%(thread)d]:  %(message)s"

# root logger for the addon
logger = logging.getLogger('hdusd')
logger.setLevel(config.log_level_show_min)

# TODO: Add creation time to this log name. Could be configurable.
file_handler = logging.FileHandler(filename=PLUGIN_ROOT_DIR / 'hdusd.log',
                                   mode='w', encoding='utf-8')
file_handler.setFormatter(logging.Formatter(FORMAT_STR))
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(stream=sys.stdout)
console_handler.setFormatter(logging.Formatter(FORMAT_STR))
logger.addHandler(console_handler)


def msg(args):
    return ", ".join(str(arg) for arg in args)


class Log:
    def __init__(self, tag):
        self.logger = logger.getChild(tag)

    def __call__(self, *args):
        self.debug(*args)

    def debug(self, *args):
        self.logger.debug(msg(args))

    def info(self, *args):
        self.logger.info(msg(args))

    def warn(self, *args):
        self.logger.warning(msg(args))

    def error(self, *args):
        self.logger.error(msg(args))

    def critical(self, *args):
        self.logger.critical(msg(args))

    def dump_args(self, func):
        """This decorator dumps out the arguments passed to a function before calling it"""
        arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]

        def echo_func(*args, **kwargs):
            self.debug("<{}>: {}{}".format(
                func.__name__,
                tuple("{}={}".format(name, arg) for name, arg in zip(arg_names, args)),
                # args if args else "",
                " {}".format(kwargs.items()) if kwargs else "",
            ))
            return func(*args, **kwargs)

        return echo_func


class LogOnce(Log):
    def __init__(self, tag):
        super().__init__(tag)

        self._cached_logs = set()

    def _cache_check(self, args):
        s = args[0]
        if s in self._cached_logs:
            return False

        self._cached_logs.add(s)
        return True

    def debug(self, *args):
        if self._cache_check(args):
            super().debug(*args)

    def info(self, *args):
        if self._cache_check(args):
            super().info(*args)

    def warn(self, *args):
        if self._cache_check(args):
            super().warn(*args)

    def error(self, *args):
        if self._cache_check(args):
            super().error(*args)

    def critical(self, *args):
        if self._cache_check(args):
            super().critical(*args)

# **********************************************************************
# Copyright 2023 Advanced Micro Devices, Inc
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
# ********************************************************************
import sys
import logging.handlers
from pathlib import Path

from . import config


ROOT_DIR = Path(__file__).parent

FORMAT_STR = "%(asctime)s %(levelname)s %(name)s [%(thread)d]:  %(message)s"

# root logger for the addon
logger = logging.getLogger('Resolver')
logger.setLevel(config.logging_level)

file_handler = logging.handlers.RotatingFileHandler(ROOT_DIR / 'resolver.log',
                                                    mode='w', encoding='utf-8', delay=True,
                                                    backupCount=config.logging_backups)
file_handler.doRollover()
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

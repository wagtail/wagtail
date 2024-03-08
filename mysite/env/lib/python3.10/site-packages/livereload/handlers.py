# -*- coding: utf-8 -*-
"""
    livereload.handlers
    ~~~~~~~~~~~~~~~~~~~

    HTTP and WebSocket handlers for livereload.

    :copyright: (c) 2013 by Hsiaoming Yang
    :license: BSD, see LICENSE for more details.
"""
import datetime
import hashlib
import os
import stat
import time
import logging
from tornado import web
from tornado import ioloop
from tornado import escape
from tornado.log import gen_log
from tornado.websocket import WebSocketHandler
from tornado.util import ObjectDict

logger = logging.getLogger('livereload')


class LiveReloadHandler(WebSocketHandler):
    waiters = set()
    watcher = None
    live_css = None
    _last_reload_time = None

    def allow_draft76(self):
        return True

    def check_origin(self, origin):
        return True

    def on_close(self):
        if self in LiveReloadHandler.waiters:
            LiveReloadHandler.waiters.remove(self)

    def send_message(self, message):
        if isinstance(message, dict):
            message = escape.json_encode(message)

        try:
            self.write_message(message)
        except:
            logger.error('Error sending message', exc_info=True)

    @classmethod
    def start_tasks(cls):
        if cls._last_reload_time:
            return

        if not cls.watcher._tasks:
            logger.info('Watch current working directory')
            cls.watcher.watch(os.getcwd())

        cls._last_reload_time = time.time()
        logger.info('Start watching changes')
        if not cls.watcher.start(cls.poll_tasks):
            logger.info('Start detecting changes')
            ioloop.PeriodicCallback(cls.poll_tasks, 800).start()

    @classmethod
    def poll_tasks(cls):
        filepath, delay = cls.watcher.examine()
        if not filepath or delay == 'forever' or not cls.waiters:
            return
        reload_time = 3

        if delay:
            reload_time = max(3 - delay, 1)
        if filepath == '__livereload__':
            reload_time = 0

        if time.time() - cls._last_reload_time < reload_time:
            # if you changed lot of files in one time
            # it will refresh too many times
            logger.info('Ignore: %s', filepath)
            return
        if delay:
            loop = ioloop.IOLoop.current()
            loop.call_later(delay, cls.reload_waiters)
        else:
            cls.reload_waiters()

    @classmethod
    def reload_waiters(cls, path=None):
        logger.info(
            'Reload %s waiters: %s',
            len(cls.waiters),
            cls.watcher.filepath,
        )

        if path is None:
            path = cls.watcher.filepath or '*'

        msg = {
            'command': 'reload',
            'path': path,
            'liveCSS': cls.live_css,
            'liveImg': True,
        }

        cls._last_reload_time = time.time()
        for waiter in cls.waiters.copy():
            try:
                waiter.write_message(msg)
            except:
                logger.error('Error sending message', exc_info=True)
                cls.waiters.remove(waiter)

    def on_message(self, message):
        """Handshake with livereload.js

        1. client send 'hello'
        2. server reply 'hello'
        3. client send 'info'
        """
        message = ObjectDict(escape.json_decode(message))
        if message.command == 'hello':
            handshake = {
                'command': 'hello',
                'protocols': [
                    'http://livereload.com/protocols/official-7',
                ],
                'serverName': 'livereload-tornado',
            }
            self.send_message(handshake)

        if message.command == 'info' and 'url' in message:
            logger.info('Browser Connected: %s' % message.url)
            LiveReloadHandler.waiters.add(self)


class MtimeStaticFileHandler(web.StaticFileHandler):
    _static_mtimes = {}  # type: typing.Dict

    @classmethod
    def get_content_modified_time(cls, abspath):
        """Returns the time that ``abspath`` was last modified.

        May be overridden in subclasses.  Should return a `~datetime.datetime`
        object or None.
        """
        stat_result = os.stat(abspath)
        modified = datetime.datetime.utcfromtimestamp(
            stat_result[stat.ST_MTIME])
        return modified

    @classmethod
    def get_content_version(cls, abspath):
        """Returns a version string for the resource at the given path.

        This class method may be overridden by subclasses.  The
        default implementation is a hash of the file's contents.

        .. versionadded:: 3.1
        """
        data = cls.get_content(abspath)
        hasher = hashlib.md5()

        mtime_data = format(cls.get_content_modified_time(abspath), "%Y-%m-%d %H:%M:%S")

        hasher.update(mtime_data.encode())

        if isinstance(data, bytes):
            hasher.update(data)
        else:
            for chunk in data:
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def _get_cached_version(cls, abs_path):
        def _load_version(abs_path):
            try:
                hsh = cls.get_content_version(abs_path)
                mtm = cls.get_content_modified_time(abs_path)

                return mtm, hsh
            except Exception:
                gen_log.error("Could not open static file %r", abs_path)
                return None, None

        with cls._lock:
            hashes = cls._static_hashes
            mtimes = cls._static_mtimes

            if abs_path not in hashes:
                mtm, hsh = _load_version(abs_path)

                hashes[abs_path] = mtm
                mtimes[abs_path] = hsh
            else:
                hsh = hashes.get(abs_path)
                mtm = mtimes.get(abs_path)

                if mtm != cls.get_content_modified_time(abs_path):
                    mtm, hsh = _load_version(abs_path)

                    hashes[abs_path] = mtm
                    mtimes[abs_path] = hsh

            if hsh:
                return hsh
        return None


class LiveReloadJSHandler(web.RequestHandler):

    def get(self):
        self.set_header('Content-Type', 'application/javascript')
        root = os.path.abspath(os.path.dirname(__file__))
        js_file = os.path.join(root, 'vendors/livereload.js')
        with open(js_file, 'rb') as f:
            self.write(f.read())


class ForceReloadHandler(web.RequestHandler):
    def get(self):
        path = self.get_argument('path', default=None) or '*'
        LiveReloadHandler.reload_waiters(path)
        self.write('ok')


class StaticFileHandler(MtimeStaticFileHandler):
    def should_return_304(self):
        return False

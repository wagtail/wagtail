# -*- coding: utf-8 -*-
"""
    livereload.watcher
    ~~~~~~~~~~~~~~~~~~

    A file watch management for LiveReload Server.

    :copyright: (c) 2013 - 2015 by Hsiaoming Yang
    :license: BSD, see LICENSE for more details.
"""

import glob
import logging
import os
import time
import sys

if sys.version_info.major < 3:
    import inspect
else:
    from inspect import signature

try:
    import pyinotify
except ImportError:
    pyinotify = None

logger = logging.getLogger('livereload')


class Watcher(object):
    """A file watcher registry."""
    def __init__(self):
        self._tasks = {}

        # modification time of filepaths for each task,
        # before and after checking for changes
        self._task_mtimes = {}
        self._new_mtimes = {}

        # setting changes
        self._changes = []

        # filepath that is changed
        self.filepath = None
        self._start = time.time()

        # list of ignored dirs
        self.ignored_dirs = ['.git', '.hg', '.svn', '.cvs']

    def ignore_dirs(self, *args):
        self.ignored_dirs.extend(args)

    def remove_dirs_from_ignore(self, *args):
        for a in args:
            self.ignored_dirs.remove(a)

    def ignore(self, filename):
        """Ignore a given filename or not."""
        _, ext = os.path.splitext(filename)
        return ext in ['.pyc', '.pyo', '.o', '.swp']

    def watch(self, path, func=None, delay=0, ignore=None):
        """Add a task to watcher.

        :param path: a filepath or directory path or glob pattern
        :param func: the function to be executed when file changed
        :param delay: Delay sending the reload message. Use 'forever' to
                      not send it. This is useful to compile sass files to
                      css, but reload on changed css files then only.
        :param ignore: A function return True to ignore a certain pattern of
                       filepath.
        """
        self._tasks[path] = {
            'func': func,
            'delay': delay,
            'ignore': ignore,
            'mtimes': {},
        }

    def start(self, callback):
        """Start the watcher running, calling callback when changes are
        observed. If this returns False, regular polling will be used."""
        return False

    def examine(self):
        """Check if there are changes. If so, run the given task.

        Returns a tuple of modified filepath and reload delay.
        """
        if self._changes:
            return self._changes.pop()

        # clean filepath
        self.filepath = None
        delays = set()
        for path in self._tasks:
            item = self._tasks[path]
            self._task_mtimes = item['mtimes']
            changed = self.is_changed(path, item['ignore'])
            if changed:
                func = item['func']
                delay = item['delay']
                if delay and isinstance(delay, float):
                    delays.add(delay)
                if func:
                    name = getattr(func, 'name', None)
                    if not name:
                        name = getattr(func, '__name__', 'anonymous')
                    logger.info(
                        "Running task: {} (delay: {})".format(name, delay))
                    if sys.version_info.major < 3:
                        sig_len = len(inspect.getargspec(func)[0])
                    else:
                        sig_len = len(signature(func).parameters)
                    if sig_len > 0 and isinstance(changed, list):
                        func(changed)
                    else:
                        func()

        if delays:
            delay = max(delays)
        else:
            delay = None
        return self.filepath, delay

    def is_changed(self, path, ignore=None):
        """Check if any filepaths have been added, modified, or removed.

        Updates filepath modification times in self._task_mtimes.
        """
        self._new_mtimes = {}
        changed = False

        if os.path.isfile(path):
            changed = self.is_file_changed(path, ignore)
        elif os.path.isdir(path):
            changed = self.is_folder_changed(path, ignore)
        else:
            changed = self.get_changed_glob_files(path, ignore)

        if not changed:
            changed = self.is_file_removed()

        self._task_mtimes.update(self._new_mtimes)
        return changed

    def is_file_removed(self):
        """Check if any filepaths have been removed since last check.

        Deletes removed paths from self._task_mtimes.
        Sets self.filepath to one of the removed paths.
        """
        removed_paths = set(self._task_mtimes) - set(self._new_mtimes)
        if not removed_paths:
            return False

        for path in removed_paths:
            self._task_mtimes.pop(path)
            # self.filepath seems purely informational, so setting one
            # of several removed files seems sufficient
            self.filepath = path
        return True

    def is_file_changed(self, path, ignore=None):
        """Check if filepath has been added or modified since last check.

        Updates filepath modification times in self._new_mtimes.
        Sets self.filepath to changed path.
        """
        if not os.path.isfile(path):
            return False

        if self.ignore(path):
            return False

        if ignore and ignore(path):
            return False

        mtime = os.path.getmtime(path)

        if path not in self._task_mtimes:
            self._new_mtimes[path] = mtime
            self.filepath = path
            return mtime > self._start

        if self._task_mtimes[path] != mtime:
            self._new_mtimes[path] = mtime
            self.filepath = path
            return True

        self._new_mtimes[path] = mtime
        return False

    def is_folder_changed(self, path, ignore=None):
        """Check if directory path has any changed filepaths."""
        for root, dirs, files in os.walk(path, followlinks=True):
            for d in self.ignored_dirs:
                if d in dirs:
                    dirs.remove(d)

            for f in files:
                if self.is_file_changed(os.path.join(root, f), ignore):
                    return True
        return False

    def get_changed_glob_files(self, path, ignore=None):
        """Check if glob path has any changed filepaths."""
        if sys.version_info[0] >=3 and sys.version_info[1] >=5:
            files = glob.glob(path, recursive=True)
        else:
            files = glob.glob(path)
        changed_files = [f for f in files if self.is_file_changed(f, ignore)]
        return changed_files


class INotifyWatcher(Watcher):
    def __init__(self):
        Watcher.__init__(self)

        self.wm = pyinotify.WatchManager()
        self.notifier = None
        self.callback = None

    def watch(self, path, func=None, delay=None, ignore=None):
        flag = pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_MODIFY
        self.wm.add_watch(path, flag, rec=True, do_glob=True, auto_add=True)
        Watcher.watch(self, path, func, delay, ignore)

    def inotify_event(self, event):
        self.callback()

    def start(self, callback):
        if not self.notifier:
            self.callback = callback

            from tornado import ioloop
            self.notifier = pyinotify.TornadoAsyncNotifier(
                self.wm, ioloop.IOLoop.instance(),
                default_proc_fun=self.inotify_event
            )
            callback()
        return True


def get_watcher_class():
    if pyinotify is None or not hasattr(pyinotify, 'TornadoAsyncNotifier'):
        return Watcher
    return INotifyWatcher

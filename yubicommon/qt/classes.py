# Copyright (c) 2014 Yubico AB
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Additional permission under GNU GPL version 3 section 7
#
# If you modify this program, or any covered work, by linking or
# combining it with the OpenSSL project's OpenSSL library (or a
# modified version of that library), containing parts covered by the
# terms of the OpenSSL or SSLeay licenses, We grant you additional
# permission to convey the resulting work. Corresponding Source for a
# non-source form of such a combination shall include the source code
# for the parts of OpenSSL used as well as that of the covered work.

from PySide import QtGui, QtCore
from .worker import Worker
import os
import sys
import time

__all__ = ['Application', 'Dialog', 'MutexLocker']

TOP_SECTION = '<b>%s</b>'
SECTION = '<br><b>%s</b>'


class Dialog(QtGui.QDialog):

    def __init__(self, *args, **kwargs):
        super(Dialog, self).__init__(*args, **kwargs)
        self.setWindowFlags(self.windowFlags()
                            ^ QtCore.Qt.WindowContextHelpButtonHint)
        self._headers = _Headers()

    @property
    def headers(self):
        return self._headers

    def section(self, title):
        return self._headers.section(title)


class _Headers(object):

    def __init__(self):
        self._first = True

    def section(self, title):
        if self._first:
            self._first = False
            section = TOP_SECTION % title
        else:
            section = SECTION % title
        return QtGui.QLabel(section)


class _MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(_MainWindow, self).__init__()

        self._widget = None

    def customEvent(self, event):
        event.callback()
        event.accept()


class Application(QtGui.QApplication):

    def __init__(self, m=None):
        super(Application, self).__init__(sys.argv)

        self.window = _MainWindow()

        if m:
            m._translate(self)

        self.worker = Worker(self.window, m)

        if getattr(sys, 'frozen', False):
            # we are running in a PyInstaller bundle
            self.basedir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            self.basedir = os.path.dirname(__file__)

    def exec_(self):
        status = super(Application, self).exec_()
        self.worker.thread().quit()
        self.deleteLater()
        time.sleep(0.01)  # Without this the process sometimes stalls.
        return status


class MutexLocker(object):

    """Drop-in replacement for QMutexLocker that can start unlocked."""

    def __init__(self, mutex, lock=True):
        self._mutex = mutex
        self._locked = False
        if lock:
            self.relock()

    def lock(self, try_lock=False):
        if try_lock:
            self._locked = self._mutex.tryLock()
        else:
            self._mutex.lock()
            self._locked = True
        return self._locked and self or None

    def relock(self):
        self.lock()

    def unlock(self):
        if self._locked:
            self._mutex.unlock()

    def __del__(self):
        self.unlock()

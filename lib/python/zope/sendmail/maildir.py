##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Read/write access to `Maildir` folders.

$Id: maildir.py 67263 2006-04-21 22:04:21Z philikon $
"""
__docformat__ = 'restructuredtext'

import os
import socket
import time
import random

from zope.interface import implements, classProvides

from zope.sendmail.interfaces import \
     IMaildirFactory, IMaildir, IMaildirMessageWriter


class Maildir(object):
    """See `zope.sendmail.interfaces.IMaildir`"""

    classProvides(IMaildirFactory)
    implements(IMaildir)

    def __init__(self, path, create=False):
        "See `zope.sendmail.interfaces.IMaildirFactory`"
        self.path = path

        def access(path):
            return os.access(path, os.F_OK)

        subdir_cur = os.path.join(path, 'cur')
        subdir_new = os.path.join(path, 'new')
        subdir_tmp = os.path.join(path, 'tmp')

        if create and not access(path):
            os.mkdir(path)
            os.mkdir(subdir_cur)
            os.mkdir(subdir_new)
            os.mkdir(subdir_tmp)
            maildir = True
        else:
            maildir = (os.path.isdir(subdir_cur) and os.path.isdir(subdir_new)
                       and os.path.isdir(subdir_tmp))
        if not maildir:
            raise ValueError('%s is not a Maildir folder' % path)

    def __iter__(self):
        "See `zope.sendmail.interfaces.IMaildir`"
        join = os.path.join
        subdir_cur = join(self.path, 'cur')
        subdir_new = join(self.path, 'new')
        # http://www.qmail.org/man/man5/maildir.html says:
        #     "It is a good idea for readers to skip all filenames in new
        #     and cur starting with a dot.  Other than this, readers
        #     should not attempt to parse filenames."
        new_messages = [join(subdir_new, x) for x in os.listdir(subdir_new)
                        if not x.startswith('.')]
        cur_messages = [join(subdir_cur, x) for x in os.listdir(subdir_cur)
                        if not x.startswith('.')]
        return iter(new_messages + cur_messages)

    def newMessage(self):
        "See `zope.sendmail.interfaces.IMaildir`"
        # NOTE: http://www.qmail.org/man/man5/maildir.html says, that the first
        #       step of the delivery process should be a chdir.  Chdirs and
        #       threading do not mix.  Is that chdir really necessary?
        join = os.path.join
        subdir_tmp = join(self.path, 'tmp')
        subdir_new = join(self.path, 'new')
        pid = os.getpid()
        host = socket.gethostname()
        randmax = 0x7fffffff
        counter = 0
        while True:
            timestamp = int(time.time())
            unique = '%d.%d.%s.%d' % (timestamp, pid, host,
                                      random.randrange(randmax))
            filename = join(subdir_tmp, unique)
            try:
                fd = os.open(filename, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0600)
            except OSError:
                # File exists
                counter += 1
                if counter >= 1000:
                    raise RuntimeError("Failed to create unique file name"
                                       " in %s, are we under a DoS attack?"
                                       % subdir_tmp)
                # NOTE: maildir.html (see above) says I should sleep for 2
                time.sleep(0.1)
            else:
                break
        return MaildirMessageWriter(os.fdopen(fd, 'w'), filename,
                                    join(subdir_new, unique))


class MaildirMessageWriter(object):
    """See `zope.sendmail.interfaces.IMaildirMessageWriter`"""

    implements(IMaildirMessageWriter)

    def __init__(self, fd, filename, new_filename):
        self._filename = filename
        self._new_filename = new_filename
        self._fd = fd
        self._closed = False
        self._aborted = False

    def write(self, data):
        self._fd.write(data)

    def writelines(self, lines):
        self._fd.writelines(lines)

    def commit(self):
        if self._closed and self._aborted:
            raise RuntimeError('Cannot commit, message already aborted')
        elif not self._closed:
            self._closed = True
            self._aborted = False
            self._fd.close()
            os.rename(self._filename, self._new_filename)
            # NOTE: the same maildir.html says it should be a link, followed by
            #       unlink.  But Win32 does not necessarily have hardlinks!

    def abort(self):
        if not self._closed:
            self._closed = True
            self._aborted = True
            self._fd.close()
            os.unlink(self._filename)

    # should there be a __del__ that does abort()?

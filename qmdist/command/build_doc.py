########################################################################
#
# File:   build_doc.py
# Author: Stefan Seefeld
# Date:   2003-09-01
#
# Contents:
#   command to build documentation as an extension to distutils
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

from distutils.command import build
from distutils.spawn import spawn, find_executable
from distutils.dep_util import newer, newer_group
from distutils.dir_util import copy_tree, remove_tree
from distutils.file_util import copy_file
import os
import os.path
import string
import glob

def find_file(paths, predicate):
    """Return a file satisfying 'predicate' from 'paths'.

    'paths' -- A sequence of glob patterns.

    'predicate' -- A callable taking a single string as an argument.

    returns -- The name of the first file matching one of the 'paths'
    and 'predicate'."""
    for path in paths:
        matches = filter(predicate, glob.glob(path))
        if matches:
            return matches[0]
    return None


class build_doc(build.build):
    """Defines the specific procedure to build QMTest's documentation.

    As this command is only ever used on 'posix' platforms, no effort
    has been made to make this code portable to other platforms such
    as 'nt'."""

    description = "build documentation"

    def call_jade(self, jade, args, dcl, type, src, builddir):
        """Runs 'jade' in a subprocess to process a docbook file.

        'jade' -- The jade executable with its full path.

        'args' -- A sequence of arguments to be passed.

        'dcl' -- An sgml declaration file for xml.

        'type' -- The output type to be generated.

        'src' -- The xml (master) source file to be processed.

        'builddir' -- The directory from which to call jade."""
        cwd = os.getcwd()
        # Use an absolute path so that calls to chdir do not invalidate
        # the name.
        src = os.path.abspath(src)
        builddir = os.path.join(self.build_temp, builddir)
        if (type == 'sgml'):
            # The stylesheet used for html output sets
            # 'html' to be the output directory. Jade
            # expects that to exist.
            self.mkpath(builddir + '/html')
        else:
            self.mkpath(builddir)
            
        os.chdir(builddir)            
        cmd = [jade] + args + ['-t', type]
        cmd += ['-d', os.path.join(cwd, 'doc', 'qm-%s.dsl'%type)]
        cmd += [dcl]
        cmd += [src]
        self.announce(string.join(cmd, ' '))
        spawn(cmd)
        os.chdir(cwd)


    def run(self):
        """Run this command, i.e. do the actual document generation.

        As this command requires 'jade', it will do nothing if
        that couldn't be found in the default path."""

        source_files = map(os.path.normpath,
                           ['qm/test/doc/manual.xml',
                            'qm/test/doc/introduction.xml',
                            'qm/test/doc/tour.xml',
                            'qm/test/doc/reference.xml'])

        jade = find_executable('jade')
        dcl = find_file(map(os.path.normpath,
                            ['/usr/share/doc/jade*/pubtext/xml.dcl',
                             '/usr/share/doc/openjade*/pubtext/xml.dcl',
                             '/usr/doc/jade*/pubtext/xml.dcl',
                             '/usr/share/sgml/declaration/xml.dcl']),
                        os.path.isfile)

        stylesheets = find_file(map(os.path.normpath,
                                    ['/usr/lib/sgml/stylesheets/docbook',
                                     '/usr/lib/sgml/stylesheets/dsssl/docbook',
                                     '/usr/share/sgml/docbook/dsssl-stylesheets']),
                                os.path.isdir)

        dtd = find_file(map(os.path.normpath,
                            ['/usr/lib/sgml',
                             '/usr/share/sgml/docbook']),
                        os.path.isdir)

        if not jade or not dcl or not stylesheets or not dtd:
            self.warn("can't build documentation")
            return

        #
        # Build html output.
        #
        target = os.path.normpath(self.build_lib + '/qm/test/doc/html')
        if newer_group(source_files, target):
            self.announce("building html manual")
            # Remove the target first such that its new mtime reflects
            # this build.
            if os.path.isdir(target): remove_tree(target)
            self.call_jade(jade, ['-D%s'%dtd, '-D%s'%stylesheets],
                           dcl, 'sgml',
                           os.path.normpath('qm/test/doc/manual.xml'),
                           os.path.normpath('qm/test/doc'))
            tidy = find_executable('tidy')
            if tidy:
                for f in glob.glob(map(os.path.normpath,
                                       self.build_temp + '/qm/test/doc/html/*.html')):
                    spawn([tidy,
                           '-wrap', '72', '-i',
                           '--indent-spaces', '1',
                           '-f', '/dev/null',
                           '-asxml', '-modify', f])
            if self.build_temp != self.build_lib:
                src = os.path.normpath(self.build_temp + '/qm/test/doc/html')
                dst = target
                self.mkpath(dst)
                copy_tree(src, dst, 1, 1, 0, 1,
                          self.verbose, self.dry_run)

        #
        # Build tex output.
        #
        target = os.path.normpath(self.build_lib + '/qm/test/doc/print/manual.tex')
        if newer_group(source_files, target):
            self.announce("building tex manual")
            # Remove the target first such that its new mtime reflects
            # this build.
            if os.path.isfile(target): os.remove(target)
            self.call_jade(jade,
                           ['-D%s'%dtd, '-D%s'%stylesheets, '-o', 'manual.tex'],
                           dcl, 'tex',
                           os.path.normpath('qm/test/doc/manual.xml'),
                           os.path.normpath('qm/test/doc'))

            # Jade places the output TeX source file in the current directory,
            # so move it where we want it afterwards.
            # We have to change -- into -{-} so that TeX does not generate long 
            # dashes.  This is a bug in Jade.
            cwd = os.getcwd()
            self.mkpath(self.build_temp + '/qm/test/doc/print')
            os.chdir(os.path.normpath(self.build_temp + '/qm/test/doc'))
            self.spawn(['sh', '-c',
                        'sed -e "s|--|-{-}|g" < manual.tex > print/manual.tex'])
            os.remove('manual.tex')
            os.chdir(cwd)
            if self.build_temp != self.build_lib:
                src = os.path.normpath(self.build_temp + '/qm/test/doc/print/manual.tex')
                dst = target
                self.mkpath(os.path.dirname(dst))
                copy_file(src, target,
                          1, 1, 1, None, self.verbose, self.dry_run)

        #
        # Build pdf output.
        #
        target = os.path.normpath(self.build_lib + '/qm/test/doc/print/manual.pdf')
        if newer_group(source_files, target):
            self.announce("building pdf manual")
            # Remove the target first such that its new mtime reflects
            # this build.
            if os.path.isfile(target): os.remove(target)
            cwd = os.getcwd()
            os.chdir(os.path.normpath(self.build_temp + '/qm/test/doc/print/'))
            self.spawn(['pdfjadetex', 'manual.tex'])
            self.spawn(['pdfjadetex', 'manual.tex'])
            self.spawn(['pdfjadetex', 'manual.tex'])
            os.chdir(cwd)
            if self.build_temp != self.build_lib:
                src = os.path.normpath(self.build_temp + '/qm/test/doc/print/manual.pdf')
                dst = target
                self.mkpath(os.path.dirname(dst))
                copy_file(src, target,
                          1, 1, 1, None, self.verbose, self.dry_run)

        #
        # Build reference manual via 'happydoc'.
        #
        happydoc = find_executable('happydoc')
        if (happydoc):
            self.announce("building reference manual")
            spawn(['happydoc', 'qm'])

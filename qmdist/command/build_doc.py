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
from   os.path import normpath
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

        # Use an absolute path so that calls to chdir do not invalidate
        # the name.
        src = os.path.abspath(src)
        builddir = os.path.dirname(src)
        if (type == 'sgml'):
            # The stylesheet used for html output sets
            # 'html' to be the output directory. Jade
            # expects that to exist.
            self.mkpath(builddir + '/html')
        else:
            self.mkpath(builddir)

        cwd = os.getcwd()
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

        source_files = map(normpath,
                           ['qm/test/doc/manual.xml',
                            'qm/test/doc/introduction.xml',
                            'qm/test/doc/tour.xml',
                            'qm/test/doc/reference.xml'])
        
        jade = find_executable('jade')
        dcl = find_file(map(normpath,
                            ['/usr/share/doc/jade*/pubtext/xml.dcl',
                             '/usr/share/doc/openjade*/pubtext/xml.dcl',
                             '/usr/doc/jade*/pubtext/xml.dcl',
                             '/usr/share/sgml/declaration/xml.dcl']),
                        os.path.isfile)

        stylesheets = find_file(map(normpath,
                                    ['/usr/lib/sgml/stylesheets/docbook',
                                     '/usr/lib/sgml/stylesheets/dsssl/docbook',
                                     '/usr/share/sgml/docbook/dsssl-stylesheets']),
                                os.path.isdir)

        dtd = find_file(map(normpath,
                            ['/usr/lib/sgml',
                             '/usr/share/sgml/docbook']),
                        os.path.isdir)

        if not jade or not dcl or not stylesheets or not dtd:
            self.warn("cannot build documentation")
            return

        # All files that are generated below are generated in the
        # source tree.  That is the only way that Distutils will
        # install the documentation as data files (in "share") rather
        # than as program files (in "lib").
        
        #
        # Build html output.
        #
        html_dir = os.path.join("qm", "test", "doc", "html")
        if newer_group(source_files, html_dir):
            self.announce("building html manual")
            # Remove the html_dir first such that its new mtime reflects
            # this build.
            if os.path.isdir(html_dir): remove_tree(html_dir)
            self.call_jade(jade, ['-D%s'%dtd, '-D%s'%stylesheets],
                           dcl, 'sgml',
                           normpath('qm/test/doc/manual.xml'),
                           normpath('qm/test/doc'))
            tidy = find_executable('tidy')
            if tidy:
                for f in glob.glob(normpath('/qm/test/doc/html/*.html')):
                    spawn([tidy,
                           '-wrap', '72', '-i',
                           '--indent-spaces', '1',
                           '-f', '/dev/null',
                           '-asxml', '-modify', f])

        target = normpath("qm/test/doc/print/manual.tex")
        if newer_group(source_files, target):
            self.announce("building tex manual")
            # Remove the target first such that its new mtime reflects
            # this build.
            if os.path.isfile(target): os.remove(target)
            self.call_jade(jade,
                           ['-D%s'%dtd, '-D%s'%stylesheets, '-o',
                            'manual.tex'],
                           dcl, 'tex',
                           normpath('qm/test/doc/manual.xml'),
                           normpath('qm/test/doc'))

            # Jade places the output TeX source file in the current
            # directory, so move it where we want it afterwards.  We have
            # to change -- into -{-} so that TeX does not generate long
            # dashes.  This is a bug in Jade.
            orig_tex_manual = normpath("qm/test/doc/manual.tex")
            self.mkpath(normpath("qm/test/doc/print"))
            self.spawn(['sh', '-c',
                        ('sed -e "s|--|-{-}|g" < %s > %s'
                         % (orig_tex_manual,
                            normpath("qm/test/doc/print/manual.tex")))])
            os.remove(orig_tex_manual)

        #
        # Build pdf output.
        #
        pdf_file = os.path.join("qm", "test", "doc", "print", "manual.pdf")
        if newer_group(source_files, pdf_file):
            self.announce("building pdf manual")
            # Remove the pdf_file first such that its new mtime reflects
            # this build.
            if os.path.isfile(pdf_file): os.remove(pdf_file)
            cwd = os.getcwd()
            os.chdir("qm/test/doc/print")
            for i in xrange(3):
                self.spawn(['pdfjadetex', "manual.tex"])
            os.chdir(cwd)

        #
        # Build reference manual via 'happydoc'.
        #
        happydoc = find_executable('happydoc')
        if (happydoc):
            self.announce("building reference manual")
            spawn(['happydoc', 'qm'])

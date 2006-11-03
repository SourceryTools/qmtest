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
from distutils.file_util import copy_file, move_file
import os, os.path
from   shutil import *

class build_html_tutorial(build.build):
    """Defines the procedure to build the html tutorial."""

    description = "build html tutorial"

    def run(self):
        """Run this command, i.e. do the actual document generation."""

        tempdir = os.path.abspath(os.path.join(self.build_temp, 'doc'))
        srcdir = os.getcwd()
        source_files = [os.path.abspath(p)
                        for p in ['doc/tutorial.xml',
                                  'doc/concepts.xml',
                                  'doc/cli_reference.xml',
                                  'doc/customizing.xml',
                                  'doc/extending.xml']]

        # Look for programs and supporting libraries required to build
        # DocBook documentation.
        xsltproc = find_executable('xsltproc')
        
        if not xsltproc:
            self.warn("could not find xsltproc in PATH")
            self.warn("cannot build html tutorial")
            return

        self.mkpath(tempdir)
        os.chdir(tempdir)

        if newer_group(source_files, 'html/tutorial'):
            self.announce("building html tutorial")
            if os.path.isdir('html/tutorial'): remove_tree('html/tutorial')
            self.mkpath('tutorial/html')
            cmd = xsltproc.split() + ['--novalid', '--xinclude',
                                      '-o', 'html/tutorial/',
                                      srcdir + '/doc/html.xsl',
                                      srcdir + '/doc/tutorial.xml']
            self.announce(' '.join(cmd))
            spawn(cmd)
            copy_file(srcdir + '/doc/cs.css', 'html/tutorial/cs.css')
        dest = srcdir + '/share/doc/qmtest/html/tutorial'
        if newer('html/tutorial', dest):
            rmtree(dest, True)
            copy_tree('html/tutorial', dest)

        os.chdir(srcdir)


class build_pdf_tutorial(build.build):
    """Defines the procedure to build the pdf tutorial."""

    description = "build pdf tutorial"

    def run(self):
        """Run this command, i.e. do the actual document generation."""

        tempdir = os.path.abspath(os.path.join(self.build_temp, 'doc'))
        srcdir = os.getcwd()
        source_files = [os.path.abspath(p)
                        for p in ['doc/tutorial.xml',
                                  'doc/concepts.xml',
                                  'doc/cli_reference.xml',
                                  'doc/customizing.xml',
                                  'doc/extending.xml']]

        # Look for programs and supporting libraries required to build
        # DocBook documentation.
        xsltproc = find_executable('xsltproc')
        foproc = None
        xep = False
        
        if not xsltproc:
            self.warn("could not find xsltproc in PATH")
            self.warn("cannot build tutorial")
            return

        foproc = find_executable('xep')
        if foproc:
            xsltproc += ' --stringparam xep.extensions 1'
            xep = True
        if not foproc:
            foproc = find_executable('fop')
        if not foproc:
            foproc = find_executable('xmlroff')
            if foproc: foproc += ' --compat'
        if not foproc:
            self.warn("could not find either of xep, fop, or xmlroff in PATH")
            self.warn("cannot build tutorial.pdf")
            return

        self.mkpath(tempdir)
        os.chdir(tempdir)
        if newer_group(source_files, 'print/tutorial.pdf'):
            self.announce("building pdf tutorial")
            self.mkpath('print')
            cmd = xsltproc.split() + ['--novalid', '--xinclude',
                                      '-o', 'print/tutorial.fo',
                                      srcdir + '/doc/fo.xsl',
                                      srcdir + '/doc/tutorial.xml']
            self.announce(' '.join(cmd))
            spawn(cmd)
            if xep:
                cmd = foproc.split() + ['print/tutorial.fo']
            else:
                cmd = foproc.split() + ['-o', 'print/tutorial.pdf',
                                        'print/tutorial.fo']
            self.announce(' '.join(cmd))
            spawn(cmd)
            self.mkpath(srcdir + '/share/doc/qmtest/print')
        dest = srcdir + '/share/doc/qmtest/print/tutorial.pdf'
        if newer('print/tutorial.pdf', dest):
            copy_file('print/tutorial.pdf', dest)

        os.chdir(srcdir)



class build_ref_manual(build.build):
    """Defines the procedure to build API reference manual."""

    description = "build API reference manual"

    user_options = [
        ("generator=", None, "name of the doc generator to use"),
        ("args=", None, "options to pass to the generator")
        ]

    def initialize_options(self):

        self.generator = None
        self.args = None
        build.build.initialize_options(self)

        
    def run(self):
        """Run this command, i.e. do the actual document generation."""

        tempdir = os.path.abspath(os.path.join(self.build_temp, 'doc'))
        srcdir = os.getcwd()
        self.mkpath(tempdir)

        generator = self.generator
        args = self.args

        if not generator:
            generator = find_executable('epydoc')
            if generator:
                args += ' --no-sourcecode -o share/doc/qmtest/html/manual'

        if not generator:
            generator = find_executable('happydoc')
            if generator:
                args += ' -d share/doc/qmtest/html/manual'

        if not generator:
            self.warn("could not find either of epydoc or happydoc in PATH")
        else:
            self.announce("building reference manual")
            spawn([generator] + args.split() + ['qm'])



class build_doc(build.build):
    """Defines the specific procedure to build QMTest's documentation.

    As this command is only ever used on 'posix' platforms, no effort
    has been made to make this code portable to other platforms such
    as 'nt'."""

    description = "build documentation"

    user_options = [
        ("html", None, "generate HTML documentation"),
        ("no-html", None, "do not generate HTML documentation"),
        ("pdf", None, "generate PDF documentation"),
        ("no-pdf", None, "do not generate PDF documentation"),
        ("ref-manual", None, "generate reference manual"),
        ("no-ref-manual", None, "do not generate reference manual"),
        ]

    boolean_options = [ "html", "pdf", "ref-manual" ]
    negative_opt = { "no-html" : "html",
                     "no-pdf" : "pdf",
                     "no-ref-manual" : "ref-manual" }
    
    def initialize_options(self):

        self.html = True
        self.pdf = True
        self.ref_manual = True
        build.build.initialize_options(self)

        
    def run(self):
        """Run this command, i.e. do the actual document generation."""


        tempdir = os.path.abspath(os.path.join(self.build_temp, 'doc'))
        srcdir = os.getcwd()

        self.mkpath(tempdir)

        # 
        # Write the version to a file so the tutorial can refer to it.  This
        # file contains exactly the version number -- there must be no
        # trailing newline, for example.
        #
        self.announce("writing version file")
        f = open(os.path.join(tempdir, 'qm-version'), 'w')
        f.write(self.distribution.get_version())
        f.close()

        for c in self.get_sub_commands(): 
            self.run_command(c)


    def build_html_tutorial(self) : return self.html
    def build_pdf_tutorial(self) : return self.pdf
    def build_ref_manual(self) : return self.ref_manual

    sub_commands = [('build_html_tutorial', build_html_tutorial),
                    ('build_pdf_tutorial', build_pdf_tutorial),
                    ('build_ref_manual', build_ref_manual)]


##############################################################################
#
# Copyright (c) 2004-2006 Zope Corporation and Contributors.
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
"""Test runner

$Id: testrunner.py 88055 2008-07-06 06:34:08Z andreasjung $
"""

# Too bad: For now, we depend on zope.testing.  This is because
# we want to use the latest, greatest doctest, which zope.testing
# provides.  Then again, zope.testing is generally useful.

import gc
import glob
import logging
import optparse
import os
import errno
import pdb
import re
import cStringIO
import sys
import tempfile
import threading
import time
import trace
import traceback
import types
import unittest


available_profilers = {}

try:
    import cProfile
    import pstats
except ImportError:
    pass
else:
    class CProfiler(object):
        """cProfiler"""
        def __init__(self, filepath):
            self.filepath = filepath
            self.profiler = cProfile.Profile()
            self.enable = self.profiler.enable
            self.disable = self.profiler.disable

        def finish(self):
            self.profiler.dump_stats(self.filepath)

        def loadStats(self, prof_glob):
            stats = None
            for file_name in glob.glob(prof_glob):
                if stats is None:
                    stats = pstats.Stats(file_name)
                else:
                    stats.add(file_name)
            return stats

    available_profilers['cProfile'] = CProfiler

# some Linux distributions don't include the profiler, which hotshot uses
try:
    import hotshot
    import hotshot.stats
except ImportError:
    pass
else:
    class HotshotProfiler(object):
        """hotshot interface"""

        def __init__(self, filepath):
            self.profiler = hotshot.Profile(filepath)
            self.enable = self.profiler.start
            self.disable = self.profiler.stop

        def finish(self):
            self.profiler.close()

        def loadStats(self, prof_glob):
            stats = None
            for file_name in glob.glob(prof_glob):
                loaded = hotshot.stats.load(file_name)
                if stats is None:
                    stats = loaded
                else:
                    stats.add(loaded)
            return stats

    available_profilers['hotshot'] = HotshotProfiler


real_pdb_set_trace = pdb.set_trace

# For some reason, the doctest module resets the trace callable randomly, thus
# disabling the coverage. Simply disallow the code from doing this. A real
# trace can be set, so that debugging still works.
osettrace = sys.settrace
def settrace(trace):
    if trace is None:
        return
    osettrace(trace)

class TestIgnore:

    def __init__(self, options):
        self._test_dirs = [self._filenameFormat(d[0]) + os.path.sep
                           for d in test_dirs(options, {})]
        self._ignore = {}
        self._ignored = self._ignore.get

    def names(self, filename, modulename):
        # Special case: Modules generated from text files; i.e. doctests
        if modulename == '<string>':
            return True
        filename = self._filenameFormat(filename)
        ignore = self._ignored(filename)
        if ignore is None:
            ignore = True
            if filename is not None:
                for d in self._test_dirs:
                    if filename.startswith(d):
                        ignore = False
                        break
            self._ignore[filename] = ignore
        return ignore

    def _filenameFormat(self, filename):
        return os.path.abspath(filename)

if sys.platform == 'win32':
    #on win32 drive name can be passed with different case to `names`
    #that lets e.g. the coverage profiler skip complete files
    #_filenameFormat will make sure that all drive and filenames get lowercased
    #albeit trace coverage has still problems with lowercase drive letters
    #when determining the dotted module name
    OldTestIgnore = TestIgnore

    class TestIgnore(OldTestIgnore):
        def _filenameFormat(self, filename):
            return os.path.normcase(os.path.abspath(filename))

class TestTrace(trace.Trace):
    """Simple tracer.

    >>> tracer = TestTrace(None, count=False, trace=False)

    Simple rules for use: you can't stop the tracer if it not started
    and you can't start the tracer if it already started:

    >>> tracer.stop()
    Traceback (most recent call last):
        File 'testrunner.py'
    AssertionError: can't stop if not started

    >>> tracer.start()
    >>> tracer.start()
    Traceback (most recent call last):
        File 'testrunner.py'
    AssertionError: can't start if already started

    >>> tracer.stop()
    >>> tracer.stop()
    Traceback (most recent call last):
        File 'testrunner.py'
    AssertionError: can't stop if not started
    """

    def __init__(self, options, **kw):
        trace.Trace.__init__(self, **kw)
        if options is not None:
            self.ignore = TestIgnore(options)
        self.started = False

    def start(self):
        assert not self.started, "can't start if already started"
        if not self.donothing:
            sys.settrace = settrace
            sys.settrace(self.globaltrace)
            threading.settrace(self.globaltrace)
        self.started = True

    def stop(self):
        assert self.started, "can't stop if not started"
        if not self.donothing:
            sys.settrace = osettrace
            sys.settrace(None)
            threading.settrace(None)
        self.started = False

class EndRun(Exception):
    """Indicate that the existing run call should stop

    Used to prevent additional test output after post-mortem debugging.
    """

def strip_py_ext(options, path):
    """Return path without its .py (or .pyc or .pyo) extension, or None.

    If options.usecompiled is false:
        If path ends with ".py", the path without the extension is returned.
        Else None is returned.

    If options.usecompiled is true:
        If Python is running with -O, a .pyo extension is also accepted.
        If Python is running without -O, a .pyc extension is also accepted.
    """
    if path.endswith(".py"):
        return path[:-3]
    if options.usecompiled:
        if __debug__:
            # Python is running without -O.
            ext = ".pyc"
        else:
            # Python is running with -O.
            ext = ".pyo"
        if path.endswith(ext):
            return path[:-len(ext)]
    return None

def contains_init_py(options, fnamelist):
    """Return true iff fnamelist contains a suitable spelling of __init__.py.

    If options.usecompiled is false, this is so iff "__init__.py" is in
    the list.

    If options.usecompiled is true, then "__init__.pyo" is also acceptable
    if Python is running with -O, and "__init__.pyc" is also acceptable if
    Python is running without -O.
    """
    if "__init__.py" in fnamelist:
        return True
    if options.usecompiled:
        if __debug__:
            # Python is running without -O.
            return "__init__.pyc" in fnamelist
        else:
            # Python is running with -O.
            return "__init__.pyo" in fnamelist
    return False


doctest_template = """
File "%s", line %s, in %s

%s
Want:
%s
Got:
%s
"""


def tigetnum(attr, default=None):
    """Return a value from the terminfo database.

    Terminfo is used on Unix-like systems to report various terminal attributes
    (such as width, height or the number of supported colors).

    Returns ``default`` when the ``curses`` module is not available, or when
    sys.stdout is not a terminal.
    """
    try:
        import curses
    except ImportError:
        # avoid reimporting a broken module in python 2.3
        sys.modules['curses'] = None
    else:
        try:
            curses.setupterm()
        except (curses.error, TypeError):
            # You get curses.error when $TERM is set to an unknown name
            # You get TypeError when sys.stdout is not a real file object
            # (e.g. in unit tests that use various wrappers).
            pass
        else:
            return curses.tigetnum(attr)
    return default


class OutputFormatter(object):
    """Test runner output formatter."""

    # Implementation note: be careful about printing stuff to sys.stderr.
    # It is used for interprocess communication between the parent and the
    # child test runner, when you run some test layers in a subprocess.
    # resume_layer() reasigns sys.stderr for this reason, but be careful
    # and don't store the original one in __init__ or something.

    max_width = 80

    def __init__(self, options):
        self.options = options
        self.last_width = 0
        self.compute_max_width()

    progress = property(lambda self: self.options.progress)
    verbose = property(lambda self: self.options.verbose)

    def compute_max_width(self):
        """Try to determine the terminal width."""
        # Note that doing this every time is more test friendly.
        self.max_width = tigetnum('cols', self.max_width)

    def getShortDescription(self, test, room):
        """Return a description of a test that fits in ``room`` characters."""
        room -= 1
        s = str(test)
        if len(s) > room:
            pos = s.find(" (")
            if pos >= 0:
                w = room - (pos + 5)
                if w < 1:
                    # first portion (test method name) is too long
                    s = s[:room-3] + "..."
                else:
                    pre = s[:pos+2]
                    post = s[-w:]
                    s = "%s...%s" % (pre, post)
            else:
                w = room - 4
                s = '... ' + s[-w:]

        return ' ' + s[:room]

    def info(self, message):
        """Print an informative message."""
        print message

    def info_suboptimal(self, message):
        """Print an informative message about losing some of the features.

        For example, when you run some tests in a subprocess, you lose the
        ability to use the debugger.
        """
        print message

    def error(self, message):
        """Report an error."""
        print message

    def error_with_banner(self, message):
        """Report an error with a big ASCII banner."""
        print
        print '*'*70
        self.error(message)
        print '*'*70
        print

    def profiler_stats(self, stats):
        """Report profiler stats."""
        stats.print_stats(50)

    def import_errors(self, import_errors):
        """Report test-module import errors (if any)."""
        if import_errors:
            print "Test-module import failures:"
            for error in import_errors:
                self.print_traceback("Module: %s\n" % error.module,
                                     error.exc_info),
            print

    def tests_with_errors(self, errors):
        """Report names of tests with errors (if any)."""
        if errors:
            print
            print "Tests with errors:"
            for test, exc_info in errors:
                print "  ", test

    def tests_with_failures(self, failures):
        """Report names of tests with failures (if any)."""
        if failures:
            print
            print "Tests with failures:"
            for test, exc_info in failures:
                print "  ", test

    def modules_with_import_problems(self, import_errors):
        """Report names of modules with import problems (if any)."""
        if import_errors:
            print
            print "Test-modules with import problems:"
            for test in import_errors:
                print "  " + test.module

    def format_seconds(self, n_seconds):
        """Format a time in seconds."""
        if n_seconds >= 60:
            n_minutes, n_seconds = divmod(n_seconds, 60)
            return "%d minutes %.3f seconds" % (n_minutes, n_seconds)
        else:
            return "%.3f seconds" % n_seconds

    def format_seconds_short(self, n_seconds):
        """Format a time in seconds (short version)."""
        return "%.3f s" % n_seconds

    def summary(self, n_tests, n_failures, n_errors, n_seconds):
        """Summarize the results of a single test layer."""
        print ("  Ran %s tests with %s failures and %s errors in %s."
               % (n_tests, n_failures, n_errors,
                  self.format_seconds(n_seconds)))

    def totals(self, n_tests, n_failures, n_errors, n_seconds):
        """Summarize the results of all layers."""
        print ("Total: %s tests, %s failures, %s errors in %s."
               % (n_tests, n_failures, n_errors,
                  self.format_seconds(n_seconds)))

    def list_of_tests(self, tests, layer_name):
        """Report a list of test names."""
        print "Listing %s tests:" % layer_name
        for test in tests:
            print ' ', test

    def garbage(self, garbage):
        """Report garbage generated by tests."""
        if garbage:
            print "Tests generated new (%d) garbage:" % len(garbage)
            print garbage

    def test_garbage(self, test, garbage):
        """Report garbage generated by a test."""
        if garbage:
            print "The following test left garbage:"
            print test
            print garbage

    def test_threads(self, test, new_threads):
        """Report threads left behind by a test."""
        if new_threads:
            print "The following test left new threads behind:"
            print test
            print "New thread(s):", new_threads

    def refcounts(self, rc, prev):
        """Report a change in reference counts."""
        print "  sys refcount=%-8d change=%-6d" % (rc, rc - prev)

    def detailed_refcounts(self, track, rc, prev):
        """Report a change in reference counts, with extra detail."""
        print ("  sum detail refcount=%-8d"
               " sys refcount=%-8d"
               " change=%-6d"
               % (track.n, rc, rc - prev))
        track.output()

    def start_set_up(self, layer_name):
        """Report that we're setting up a layer.

        The next output operation should be stop_set_up().
        """
        print "  Set up %s" % layer_name,
        sys.stdout.flush()

    def stop_set_up(self, seconds):
        """Report that we've set up a layer.

        Should be called right after start_set_up().
        """
        print "in %s." % self.format_seconds(seconds)

    def start_tear_down(self, layer_name):
        """Report that we're tearing down a layer.

        The next output operation should be stop_tear_down() or
        tear_down_not_supported().
        """
        print "  Tear down %s" % layer_name,
        sys.stdout.flush()

    def stop_tear_down(self, seconds):
        """Report that we've tore down a layer.

        Should be called right after start_tear_down().
        """
        print "in %s." % self.format_seconds(seconds)

    def tear_down_not_supported(self):
        """Report that we could not tear down a layer.

        Should be called right after start_tear_down().
        """
        print "... not supported"

    def start_test(self, test, tests_run, total_tests):
        """Report that we're about to run a test.

        The next output operation should be test_success(), test_error(), or
        test_failure().
        """
        self.test_width = 0
        if self.progress:
            if self.last_width:
                sys.stdout.write('\r' + (' ' * self.last_width) + '\r')

            s = "    %d/%d (%.1f%%)" % (tests_run, total_tests,
                                        tests_run * 100.0 / total_tests)
            sys.stdout.write(s)
            self.test_width += len(s)
            if self.verbose == 1:
                room = self.max_width - self.test_width - 1
                s = self.getShortDescription(test, room)
                sys.stdout.write(s)
                self.test_width += len(s)

        elif self.verbose == 1:
            sys.stdout.write('.' * test.countTestCases())

        if self.verbose > 1:
            s = str(test)
            sys.stdout.write(' ')
            sys.stdout.write(s)
            self.test_width += len(s) + 1

        sys.stdout.flush()

    def test_success(self, test, seconds):
        """Report that a test was successful.

        Should be called right after start_test().

        The next output operation should be stop_test().
        """
        if self.verbose > 2:
            s = " (%s)" % self.format_seconds_short(seconds)
            sys.stdout.write(s)
            self.test_width += len(s) + 1

    def test_error(self, test, seconds, exc_info):
        """Report that an error occurred while running a test.

        Should be called right after start_test().

        The next output operation should be stop_test().
        """
        if self.verbose > 2:
            print " (%s)" % self.format_seconds_short(seconds)
        print
        self.print_traceback("Error in test %s" % test, exc_info)
        self.test_width = self.last_width = 0

    def test_failure(self, test, seconds, exc_info):
        """Report that a test failed.

        Should be called right after start_test().

        The next output operation should be stop_test().
        """
        if self.verbose > 2:
            print " (%s)" % self.format_seconds_short(seconds)
        print
        self.print_traceback("Failure in test %s" % test, exc_info)
        self.test_width = self.last_width = 0

    def print_traceback(self, msg, exc_info):
        """Report an error with a traceback."""
        print
        print msg
        print self.format_traceback(exc_info)

    def format_traceback(self, exc_info):
        """Format the traceback."""
        v = exc_info[1]
        if isinstance(v, doctest.DocTestFailureException):
            tb = v.args[0]
        elif isinstance(v, doctest.DocTestFailure):
            tb = doctest_template % (
                v.test.filename,
                v.test.lineno + v.example.lineno + 1,
                v.test.name,
                v.example.source,
                v.example.want,
                v.got,
                )
        else:
            tb = "".join(traceback.format_exception(*exc_info))
        return tb

    def stop_test(self, test):
        """Clean up the output state after a test."""
        if self.progress:
            self.last_width = self.test_width
        elif self.verbose > 1:
            print
        sys.stdout.flush()

    def stop_tests(self):
        """Clean up the output state after a collection of tests."""
        if self.progress and self.last_width:
            sys.stdout.write('\r' + (' ' * self.last_width) + '\r')
        if self.verbose == 1 or self.progress:
            print


class ColorfulOutputFormatter(OutputFormatter):
    """Output formatter that uses ANSI color codes.

    Like syntax highlighting in your text editor, colorizing
    test failures helps the developer.
    """

    # These colors are carefully chosen to have enough contrast
    # on terminals with both black and white background.
    colorscheme = {'normal': 'normal',
                   'default': 'default',
                   'info': 'normal',
                   'suboptimal-behaviour': 'magenta',
                   'error': 'brightred',
                   'number': 'green',
                   'slow-test': 'brightmagenta',
                   'ok-number': 'green',
                   'error-number': 'brightred',
                   'filename': 'lightblue',
                   'lineno': 'lightred',
                   'testname': 'lightcyan',
                   'failed-example': 'cyan',
                   'expected-output': 'green',
                   'actual-output': 'red',
                   'character-diffs': 'magenta',
                   'diff-chunk': 'magenta',
                   'exception': 'red'}

    # Map prefix character to color in diff output.  This handles ndiff and
    # udiff correctly, but not cdiff.  In cdiff we ought to highlight '!' as
    # expected-output until we see a '-', then highlight '!' as actual-output,
    # until we see a '*', then switch back to highlighting '!' as
    # expected-output.  Nevertheless, coloried cdiffs are reasonably readable,
    # so I'm not going to fix this.
    #   -- mgedmin
    diff_color = {'-': 'expected-output',
                  '+': 'actual-output',
                  '?': 'character-diffs',
                  '@': 'diff-chunk',
                  '*': 'diff-chunk',
                  '!': 'actual-output',}

    prefixes = [('dark', '0;'),
                ('light', '1;'),
                ('bright', '1;'),
                ('bold', '1;'),]

    colorcodes = {'default': 0, 'normal': 0,
                  'black': 30,
                  'red': 31,
                  'green': 32,
                  'brown': 33, 'yellow': 33,
                  'blue': 34,
                  'magenta': 35,
                  'cyan': 36,
                  'grey': 37, 'gray': 37, 'white': 37}

    slow_test_threshold = 10.0 # seconds

    def color_code(self, color):
        """Convert a color description (e.g. 'lightgray') to a terminal code."""
        prefix_code = ''
        for prefix, code in self.prefixes:
            if color.startswith(prefix):
                color = color[len(prefix):]
                prefix_code = code
                break
        color_code = self.colorcodes[color]
        return '\033[%s%sm' % (prefix_code, color_code)

    def color(self, what):
        """Pick a named color from the color scheme"""
        return self.color_code(self.colorscheme[what])

    def colorize(self, what, message, normal='normal'):
        """Wrap message in color."""
        return self.color(what) + message + self.color(normal)

    def error_count_color(self, n):
        """Choose a color for the number of errors."""
        if n:
            return self.color('error-number')
        else:
            return self.color('ok-number')

    def info(self, message):
        """Print an informative message."""
        print self.colorize('info', message)

    def info_suboptimal(self, message):
        """Print an informative message about losing some of the features.

        For example, when you run some tests in a subprocess, you lose the
        ability to use the debugger.
        """
        print self.colorize('suboptimal-behaviour', message)

    def error(self, message):
        """Report an error."""
        print self.colorize('error', message)

    def error_with_banner(self, message):
        """Report an error with a big ASCII banner."""
        print
        print self.colorize('error', '*'*70)
        self.error(message)
        print self.colorize('error', '*'*70)
        print

    def tear_down_not_supported(self):
        """Report that we could not tear down a layer.

        Should be called right after start_tear_down().
        """
        print "...", self.colorize('suboptimal-behaviour', "not supported")

    def format_seconds(self, n_seconds, normal='normal'):
        """Format a time in seconds."""
        if n_seconds >= 60:
            n_minutes, n_seconds = divmod(n_seconds, 60)
            return "%s minutes %s seconds" % (
                        self.colorize('number', '%d' % n_minutes, normal),
                        self.colorize('number', '%.3f' % n_seconds, normal))
        else:
            return "%s seconds" % (
                        self.colorize('number', '%.3f' % n_seconds, normal))

    def format_seconds_short(self, n_seconds):
        """Format a time in seconds (short version)."""
        if n_seconds >= self.slow_test_threshold:
            color = 'slow-test'
        else:
            color = 'number'
        return self.colorize(color, "%.3f s" % n_seconds)

    def summary(self, n_tests, n_failures, n_errors, n_seconds):
        """Summarize the results."""
        sys.stdout.writelines([
            self.color('info'), '  Ran ',
            self.color('number'), str(n_tests),
            self.color('info'), ' tests with ',
            self.error_count_color(n_failures), str(n_failures),
            self.color('info'), ' failures and ',
            self.error_count_color(n_errors), str(n_errors),
            self.color('info'), ' errors in ',
            self.format_seconds(n_seconds, 'info'), '.',
            self.color('normal'), '\n'])

    def totals(self, n_tests, n_failures, n_errors, n_seconds):
        """Report totals (number of tests, failures, and errors)."""
        sys.stdout.writelines([
            self.color('info'), 'Total: ',
            self.color('number'), str(n_tests),
            self.color('info'), ' tests, ',
            self.error_count_color(n_failures), str(n_failures),
            self.color('info'), ' failures, ',
            self.error_count_color(n_errors), str(n_errors),
            self.color('info'), ' errors in ',
            self.format_seconds(n_seconds, 'info'), '.',
            self.color('normal'), '\n'])

    def print_traceback(self, msg, exc_info):
        """Report an error with a traceback."""
        print
        print self.colorize('error', msg)
        v = exc_info[1]
        if isinstance(v, doctest.DocTestFailureException):
            self.print_doctest_failure(v.args[0])
        elif isinstance(v, doctest.DocTestFailure):
            # I don't think these are ever used... -- mgedmin
            tb = self.format_traceback(exc_info)
            print tb
        else:
            tb = self.format_traceback(exc_info)
            self.print_colorized_traceback(tb)

    def print_doctest_failure(self, formatted_failure):
        """Report a doctest failure.

        ``formatted_failure`` is a string -- that's what
        DocTestSuite/DocFileSuite gives us.
        """
        color_of_indented_text = 'normal'
        colorize_diff = False
        for line in formatted_failure.splitlines():
            if line.startswith('File '):
                m = re.match(r'File "(.*)", line (\d*), in (.*)$', line)
                if m:
                    filename, lineno, test = m.groups()
                    sys.stdout.writelines([
                        self.color('normal'), 'File "',
                        self.color('filename'), filename,
                        self.color('normal'), '", line ',
                        self.color('lineno'), lineno,
                        self.color('normal'), ', in ',
                        self.color('testname'), test,
                        self.color('normal'), '\n'])
                else:
                    print line
            elif line.startswith('    '):
                if colorize_diff and len(line) > 4:
                    color = self.diff_color.get(line[4], color_of_indented_text)
                    print self.colorize(color, line)
                else:
                    print self.colorize(color_of_indented_text, line)
            else:
                colorize_diff = False
                if line.startswith('Failed example'):
                    color_of_indented_text = 'failed-example'
                elif line.startswith('Expected:'):
                    color_of_indented_text = 'expected-output'
                elif line.startswith('Got:'):
                    color_of_indented_text = 'actual-output'
                elif line.startswith('Exception raised:'):
                    color_of_indented_text = 'exception'
                elif line.startswith('Differences '):
                    color_of_indented_text = 'normal'
                    colorize_diff = True
                else:
                    color_of_indented_text = 'normal'
                print line
        print

    def print_colorized_traceback(self, formatted_traceback):
        """Report a test failure.

        ``formatted_traceback`` is a string.
        """
        for line in formatted_traceback.splitlines():
            if line.startswith('  File'):
                m = re.match(r'  File "(.*)", line (\d*), in (.*)$', line)
                if m:
                    filename, lineno, test = m.groups()
                    sys.stdout.writelines([
                        self.color('normal'), '  File "',
                        self.color('filename'), filename,
                        self.color('normal'), '", line ',
                        self.color('lineno'), lineno,
                        self.color('normal'), ', in ',
                        self.color('testname'), test,
                        self.color('normal'), '\n'])
                else:
                    print line
            elif line.startswith('    '):
                print self.colorize('failed-example', line)
            elif line.startswith('Traceback (most recent call last)'):
                print line
            else:
                print self.colorize('exception', line)
        print


def run(defaults=None, args=None):
    if args is None:
        args = sys.argv[:]

    # Set the default logging policy.
    # XXX There are no tests for this logging behavior.
    # It's not at all clear that the test runner should be doing this.
    configure_logging()

    # Control reporting flags during run
    old_reporting_flags = doctest.set_unittest_reportflags(0)

    # Check to see if we are being run as a subprocess. If we are,
    # then use the resume-layer and defaults passed in.
    if len(args) > 1 and args[1] == '--resume-layer':
        args.pop(1)
        resume_layer = args.pop(1)
        resume_number = int(args.pop(1))
        defaults = []
        while len(args) > 1 and args[1] == '--default':
            args.pop(1)
            defaults.append(args.pop(1))

        sys.stdin = FakeInputContinueGenerator()
    else:
        resume_layer = resume_number = None

    options = get_options(args, defaults)
    if options.fail:
        return True

    output = options.output

    options.testrunner_defaults = defaults
    options.resume_layer = resume_layer
    options.resume_number = resume_number

    # Make sure we start with real pdb.set_trace.  This is needed
    # to make tests of the test runner work properly. :)
    pdb.set_trace = real_pdb_set_trace

    if (options.profile
        and sys.version_info[:3] <= (2,4,1)
        and __debug__):
        output.error('Because of a bug in Python < 2.4.1, profiling '
                     'during tests requires the -O option be passed to '
                     'Python (not the test runner).')
        sys.exit()

    if options.coverage:
        tracer = TestTrace(options, trace=False, count=True)
        tracer.start()
    else:
        tracer = None

    if options.profile:
        prof_prefix = 'tests_profile.'
        prof_suffix = '.prof'
        prof_glob = prof_prefix + '*' + prof_suffix

        # if we are going to be profiling, and this isn't a subprocess,
        # clean up any stale results files
        if not options.resume_layer:
            for file_name in glob.glob(prof_glob):
                os.unlink(file_name)

        # set up the output file
        oshandle, file_path = tempfile.mkstemp(prof_suffix, prof_prefix, '.')
        profiler = available_profilers[options.profile](file_path)
        profiler.enable()

    try:
        try:
            failed = not run_with_options(options)
        except EndRun:
            failed = True
    finally:
        if tracer:
            tracer.stop()
        if options.profile:
            profiler.disable()
            profiler.finish()
            # We must explicitly close the handle mkstemp returned, else on
            # Windows this dies the next time around just above due to an
            # attempt to unlink a still-open file.
            os.close(oshandle)

    if options.profile and not options.resume_layer:
        stats = profiler.loadStats(prof_glob)
        stats.sort_stats('cumulative', 'calls')
        output.profiler_stats(stats)

    if tracer:
        coverdir = os.path.join(os.getcwd(), options.coverage)
        r = tracer.results()
        r.write_results(summary=True, coverdir=coverdir)

    doctest.set_unittest_reportflags(old_reporting_flags)

    if failed and options.exitwithstatus:
        sys.exit(1)

    return failed

def run_with_options(options, found_suites=None):
    """Find and run tests

    Passing a list of suites using the found_suites parameter will cause
    that list of suites to be used instead of attempting to load them from
    the filesystem. This is useful for unit testing the test runner.

    Returns True if all tests passed, or False if there were any failures
    of any kind.
    """

    global _layer_name_cache
    _layer_name_cache = {} # Reset to enforce test isolation

    output = options.output

    if options.resume_layer:
        original_stderr = sys.stderr
        sys.stderr = sys.stdout
    elif options.verbose:
        if options.all:
            msg = "Running tests at all levels"
        else:
            msg = "Running tests at level %d" % options.at_level
        output.info(msg)


    old_threshold = gc.get_threshold()
    if options.gc:
        if len(options.gc) > 3:
            output.error("Too many --gc options")
            sys.exit(1)
        if options.gc[0]:
            output.info("Cyclic garbage collection threshold set to: %s" %
                        repr(tuple(options.gc)))
        else:
            output.info("Cyclic garbage collection is disabled.")

        gc.set_threshold(*options.gc)

    old_flags = gc.get_debug()
    if options.gc_option:
        new_flags = 0
        for op in options.gc_option:
            new_flags |= getattr(gc, op)
        gc.set_debug(new_flags)

    old_reporting_flags = doctest.set_unittest_reportflags(0)
    reporting_flags = 0
    if options.ndiff:
        reporting_flags = doctest.REPORT_NDIFF
    if options.udiff:
        if reporting_flags:
            output.error("Can only give one of --ndiff, --udiff, or --cdiff")
            sys.exit(1)
        reporting_flags = doctest.REPORT_UDIFF
    if options.cdiff:
        if reporting_flags:
            output.error("Can only give one of --ndiff, --udiff, or --cdiff")
            sys.exit(1)
        reporting_flags = doctest.REPORT_CDIFF
    if options.report_only_first_failure:
        reporting_flags |= doctest.REPORT_ONLY_FIRST_FAILURE

    if reporting_flags:
        doctest.set_unittest_reportflags(reporting_flags)
    else:
        doctest.set_unittest_reportflags(old_reporting_flags)


    # Add directories to the path
    for path in options.path:
        if path not in sys.path:
            sys.path.append(path)

    remove_stale_bytecode(options)

    tests_by_layer_name = find_tests(options, found_suites)

    ran = 0
    failures = []
    errors = []
    nlayers = 0
    import_errors = tests_by_layer_name.pop(None, None)

    output.import_errors(import_errors)

    if 'unit' in tests_by_layer_name:
        tests = tests_by_layer_name.pop('unit')
        if (not options.non_unit) and not options.resume_layer:
            if options.layer:
                should_run = False
                for pat in options.layer:
                    if pat('unit'):
                        should_run = True
                        break
            else:
                should_run = True

            if should_run:
                if options.list_tests:
                    output.list_of_tests(tests, 'unit')
                else:
                    output.info("Running unit tests:")
                    nlayers += 1
                    ran += run_tests(options, tests, 'unit', failures, errors)

    setup_layers = {}

    layers_to_run = list(ordered_layers(tests_by_layer_name))
    if options.resume_layer is not None:
        layers_to_run = [
            (layer_name, layer, tests)
            for (layer_name, layer, tests) in layers_to_run
            if layer_name == options.resume_layer
        ]
    elif options.layer:
        layers_to_run = [
            (layer_name, layer, tests)
            for (layer_name, layer, tests) in layers_to_run
            if filter(None, [pat(layer_name) for pat in options.layer])
        ]


    if options.list_tests:
        for layer_name, layer, tests in layers_to_run:
            output.list_of_tests(tests, layer_name)
        return True

    start_time = time.time()

    for layer_name, layer, tests in layers_to_run:
        nlayers += 1
        try:
            ran += run_layer(options, layer_name, layer, tests,
                             setup_layers, failures, errors)
        except CanNotTearDown:
            setup_layers = None
            if not options.resume_layer:
                ran += resume_tests(options, layer_name, layers_to_run,
                                    failures, errors)
                break

    if setup_layers:
        if options.resume_layer == None:
            output.info("Tearing down left over layers:")
        tear_down_unneeded(options, (), setup_layers, True)

    total_time = time.time() - start_time

    if options.resume_layer:
        sys.stdout.close()
        # Communicate with the parent.  The protocol is obvious:
        print >> original_stderr, ran, len(failures), len(errors)
        for test, exc_info in failures:
            print >> original_stderr, ' '.join(str(test).strip().split('\n'))
        for test, exc_info in errors:
            print >> original_stderr, ' '.join(str(test).strip().split('\n'))

    else:
        if options.verbose:
            output.tests_with_errors(errors)
            output.tests_with_failures(failures)

        if nlayers != 1:
            output.totals(ran, len(failures), len(errors), total_time)

        output.modules_with_import_problems(import_errors)

    doctest.set_unittest_reportflags(old_reporting_flags)

    if options.gc_option:
        gc.set_debug(old_flags)

    if options.gc:
        gc.set_threshold(*old_threshold)

    return not bool(import_errors or failures or errors)


def run_tests(options, tests, name, failures, errors):
    repeat = options.repeat or 1
    repeat_range = iter(range(repeat))
    ran = 0

    output = options.output

    gc.collect()
    lgarbage = len(gc.garbage)

    sumrc = 0
    if options.report_refcounts:
        if options.verbose:
            track = TrackRefs()
        rc = sys.gettotalrefcount()

    for iteration in repeat_range:
        if repeat > 1:
            output.info("Iteration %d" % (iteration + 1))

        if options.verbose > 0 or options.progress:
            output.info('  Running:')
        result = TestResult(options, tests, layer_name=name)

        t = time.time()

        if options.post_mortem:
            # post-mortem debugging
            for test in tests:
                if result.shouldStop:
                    break
                result.startTest(test)
                state = test.__dict__.copy()
                try:
                    try:
                        test.debug()
                    except KeyboardInterrupt:
                        raise
                    except:
                        result.addError(
                            test,
                            sys.exc_info()[:2] + (sys.exc_info()[2].tb_next, ),
                            )
                    else:
                        result.addSuccess(test)
                finally:
                    result.stopTest(test)
                test.__dict__.clear()
                test.__dict__.update(state)

        else:
            # normal
            for test in tests:
                if result.shouldStop:
                    break
                state = test.__dict__.copy()
                test(result)
                test.__dict__.clear()
                test.__dict__.update(state)

        t = time.time() - t
        output.stop_tests()
        failures.extend(result.failures)
        errors.extend(result.errors)
        output.summary(result.testsRun, len(result.failures), len(result.errors), t)
        ran = result.testsRun

        gc.collect()
        if len(gc.garbage) > lgarbage:
            output.garbage(gc.garbage[lgarbage:])
            lgarbage = len(gc.garbage)

        if options.report_refcounts:

            # If we are being tested, we don't want stdout itself to
            # foul up the numbers. :)
            try:
                sys.stdout.getvalue()
            except AttributeError:
                pass

            prev = rc
            rc = sys.gettotalrefcount()
            if options.verbose:
                track.update()
                if iteration > 0:
                    output.detailed_refcounts(track, rc, prev)
                else:
                    track.delta = None
            elif iteration > 0:
                output.refcounts(rc, prev)

    return ran

def run_layer(options, layer_name, layer, tests, setup_layers,
              failures, errors):

    output = options.output
    gathered = []
    gather_layers(layer, gathered)
    needed = dict([(l, 1) for l in gathered])
    if options.resume_number != 0:
        output.info("Running %s tests:" % layer_name)
    tear_down_unneeded(options, needed, setup_layers)

    if options.resume_layer != None:
        output.info_suboptimal( "  Running in a subprocess.")

    try:
        setup_layer(options, layer, setup_layers)
    except EndRun:
        raise
    except Exception:
        f = cStringIO.StringIO()
        traceback.print_exc(file=f)
        output.error(f.getvalue())
        errors.append((SetUpLayerFailure(), sys.exc_info()))
        return 0
    else:
        return run_tests(options, tests, layer_name, failures, errors)

class SetUpLayerFailure(unittest.TestCase):
    def runTest(self):
        "Layer set up failure."

def resume_tests(options, layer_name, layers, failures, errors):
    output = options.output
    layers = [l for (l, _, _) in layers]
    layers = layers[layers.index(layer_name):]
    rantotal = 0
    resume_number = 0
    for layer_name in layers:
        args = [sys.executable,
                options.original_testrunner_args[0],
                '--resume-layer', layer_name, str(resume_number),
                ]
        resume_number += 1
        for d in options.testrunner_defaults:
            args.extend(['--default', d])

        args.extend(options.original_testrunner_args[1:])

        # this is because of a bug in Python (http://www.python.org/sf/900092)
        if (options.profile == 'hotshot'
            and sys.version_info[:3] <= (2,4,1)):
            args.insert(1, '-O')

        if sys.platform.startswith('win'):
            args = args[0] + ' ' + ' '.join([
                ('"' + a.replace('\\', '\\\\').replace('"', '\\"') + '"')
                for a in args[1:]
                ])

        subin, subout, suberr = os.popen3(args)
        while True:
            try:
                for l in subout:
                    sys.stdout.write(l)
            except IOError, e:
                if e.errno == errno.EINTR:
                    # If the subprocess dies before we finish reading its
                    # output, a SIGCHLD signal can interrupt the reading.
                    # The correct thing to to in that case is to retry.
                    continue
                output.error("Error reading subprocess output for %s" % layer_name)
                output.info(str(e))
            else:
                break

        line = suberr.readline()
        try:
            ran, nfail, nerr = map(int, line.strip().split())
        except KeyboardInterrupt:
            raise
        except:
            raise SubprocessError(line+suberr.read())

        while nfail > 0:
            nfail -= 1
            failures.append((suberr.readline().strip(), None))
        while nerr > 0:
            nerr -= 1
            errors.append((suberr.readline().strip(), None))

        rantotal += ran

    return rantotal


class SubprocessError(Exception):
    """An error occurred when running a subprocess
    """

class CanNotTearDown(Exception):
    "Couldn't tear down a test"

def tear_down_unneeded(options, needed, setup_layers, optional=False):
    # Tear down any layers not needed for these tests. The unneeded
    # layers might interfere.
    unneeded = [l for l in setup_layers if l not in needed]
    unneeded = order_by_bases(unneeded)
    unneeded.reverse()
    output = options.output
    for l in unneeded:
        output.start_tear_down(name_from_layer(l))
        t = time.time()
        try:
            if hasattr(l, 'tearDown'):
                l.tearDown()
        except NotImplementedError:
            output.tear_down_not_supported()
            if not optional:
                raise CanNotTearDown(l)
        else:
            output.stop_tear_down(time.time() - t)
        del setup_layers[l]


cant_pm_in_subprocess_message = """
Can't post-mortem debug when running a layer as a subprocess!
Try running layer %r by itself.
"""

def setup_layer(options, layer, setup_layers):
    assert layer is not object
    output = options.output
    if layer not in setup_layers:
        for base in layer.__bases__:
            if base is not object:
                setup_layer(options, base, setup_layers)
        output.start_set_up(name_from_layer(layer))
        t = time.time()
        if hasattr(layer, 'setUp'):
            try:
                layer.setUp()
            except Exception:
                if options.post_mortem:
                    if options.resume_layer:
                        options.output.error_with_banner(
                            cant_pm_in_subprocess_message
                            % options.resume_layer)
                        raise
                    else:
                        post_mortem(sys.exc_info())
                else:
                    raise
                    
        output.stop_set_up(time.time() - t)
        setup_layers[layer] = 1

def dependencies(bases, result):
    for base in bases:
        result[base] = 1
        dependencies(base.__bases__, result)

class TestResult(unittest.TestResult):

    def __init__(self, options, tests, layer_name=None):
        unittest.TestResult.__init__(self)
        self.options = options
        # Calculate our list of relevant layers we need to call testSetUp
        # and testTearDown on.
        if layer_name != 'unit':
            layers = []
            gather_layers(layer_from_name(layer_name), layers)
            self.layers = order_by_bases(layers)
        else:
            self.layers = []
        count = 0
        for test in tests:
            count += test.countTestCases()
        self.count = count

    def testSetUp(self):
        """A layer may define a setup method to be called before each
        individual test.
        """
        for layer in self.layers:
            if hasattr(layer, 'testSetUp'):
                layer.testSetUp()

    def testTearDown(self):
        """A layer may define a teardown method to be called after each
           individual test.

           This is useful for clearing the state of global
           resources or resetting external systems such as relational
           databases or daemons.
        """
        for layer in self.layers[-1::-1]:
            if hasattr(layer, 'testTearDown'):
                layer.testTearDown()

    def startTest(self, test):
        self.testSetUp()
        unittest.TestResult.startTest(self, test)
        testsRun = self.testsRun - 1 # subtract the one the base class added
        count = test.countTestCases()
        self.testsRun = testsRun + count

        self.options.output.start_test(test, self.testsRun, self.count)

        self._threads = threading.enumerate()
        self._start_time = time.time()

    def addSuccess(self, test):
        t = max(time.time() - self._start_time, 0.0)
        self.options.output.test_success(test, t)

    def addError(self, test, exc_info):
        self.options.output.test_error(test, time.time() - self._start_time,
                                       exc_info)

        unittest.TestResult.addError(self, test, exc_info)

        if self.options.post_mortem:
            if self.options.resume_layer:
                self.options.output.error_with_banner("Can't post-mortem debug"
                                                      " when running a layer"
                                                      " as a subprocess!")
            else:
                post_mortem(exc_info)

    def addFailure(self, test, exc_info):
        self.options.output.test_failure(test, time.time() - self._start_time,
                                         exc_info)

        unittest.TestResult.addFailure(self, test, exc_info)

        if self.options.post_mortem:
            # XXX: mgedmin: why isn't there a resume_layer check here like
            # in addError?
            post_mortem(exc_info)

    def stopTest(self, test):
        self.testTearDown()
        self.options.output.stop_test(test)

        if gc.garbage:
            self.options.output.test_garbage(test, gc.garbage)
            # TODO: Perhaps eat the garbage here, so that the garbage isn't
            #       printed for every subsequent test.

        # Did the test leave any new threads behind?
        new_threads = [t for t in threading.enumerate()
                         if (t.isAlive()
                             and
                             t not in self._threads)]
        if new_threads:
            self.options.output.test_threads(test, new_threads)


class FakeInputContinueGenerator:

    def readline(self):
        print  'c\n'
        print '*'*70
        print ("Can't use pdb.set_trace when running a layer"
               " as a subprocess!")
        print '*'*70
        print
        return 'c\n'


def post_mortem(exc_info):
    err = exc_info[1]
    if isinstance(err, (doctest.UnexpectedException, doctest.DocTestFailure)):

        if isinstance(err, doctest.UnexpectedException):
            exc_info = err.exc_info

            # Print out location info if the error was in a doctest
            if exc_info[2].tb_frame.f_code.co_filename == '<string>':
                print_doctest_location(err)

        else:
            print_doctest_location(err)
            # Hm, we have a DocTestFailure exception.  We need to
            # generate our own traceback
            try:
                exec ('raise ValueError'
                      '("Expected and actual output are different")'
                      ) in err.test.globs
            except:
                exc_info = sys.exc_info()

    print "%s:" % (exc_info[0], )
    print exc_info[1]
    pdb.post_mortem(exc_info[2])
    raise EndRun

def print_doctest_location(err):
    # This mimics pdb's output, which gives way cool results in emacs :)
    filename = err.test.filename
    if filename.endswith('.pyc'):
        filename = filename[:-1]
    print "> %s(%s)_()" % (filename, err.test.lineno+err.example.lineno+1)

def ordered_layers(tests_by_layer_name):
    layer_names = dict([(layer_from_name(layer_name), layer_name)
                        for layer_name in tests_by_layer_name])
    for layer in order_by_bases(layer_names):
        layer_name = layer_names[layer]
        yield layer_name, layer, tests_by_layer_name[layer_name]

def gather_layers(layer, result):
    if layer is not object:
        result.append(layer)
    for b in layer.__bases__:
        gather_layers(b, result)

def layer_from_name(layer_name):
    """Return the layer for the corresponding layer_name by discovering
       and importing the necessary module if necessary.

       Note that a name -> layer cache is maintained by name_from_layer
       to allow locating layers in cases where it would otherwise be
       impossible.
    """
    global _layer_name_cache
    if _layer_name_cache.has_key(layer_name):
        return _layer_name_cache[layer_name]
    layer_names = layer_name.split('.')
    layer_module, module_layer_name = layer_names[:-1], layer_names[-1]
    return getattr(import_name('.'.join(layer_module)), module_layer_name)

def order_by_bases(layers):
    """Order the layers from least to most specific (bottom to top)
    """
    named_layers = [(name_from_layer(layer), layer) for layer in layers]
    named_layers.sort()
    named_layers.reverse()
    gathered = []
    for name, layer in named_layers:
        gather_layers(layer, gathered)
    gathered.reverse()
    seen = {}
    result = []
    for layer in gathered:
        if layer not in seen:
            seen[layer] = 1
            if layer in layers:
                result.append(layer)
    return result

_layer_name_cache = {}

def name_from_layer(layer):
    """Determine a name for the Layer using the namespace to avoid conflicts.

    We also cache a name -> layer mapping to enable layer_from_name to work
    in cases where the layer cannot be imported (such as layers defined
    in doctests)
    """
    if layer.__module__ == '__builtin__':
        name = layer.__name__
    else:
        name = layer.__module__ + '.' + layer.__name__
    _layer_name_cache[name] = layer
    return name

def find_tests(options, found_suites=None):
    """Creates a dictionary mapping layer name to a suite of tests to be run
    in that layer.

    Passing a list of suites using the found_suites parameter will cause
    that list of suites to be used instead of attempting to load them from
    the filesystem. This is useful for unit testing the test runner.
    """
    suites = {}
    if found_suites is None:
        found_suites = find_suites(options)
    for suite in found_suites:
        for test, layer_name in tests_from_suite(suite, options):
            suite = suites.get(layer_name)
            if not suite:
                suite = suites[layer_name] = unittest.TestSuite()
            suite.addTest(test)
    return suites

def tests_from_suite(suite, options, dlevel=1, dlayer='unit'):
    """Returns a sequence of (test, layer_name)

    The tree of suites is recursively visited, with the most specific
    layer taking precedence. So if a TestCase with a layer of 'foo' is
    contained in a TestSuite with a layer of 'bar', the test case would be
    returned with 'foo' as the layer.

    Tests are also filtered out based on the test level and test selection
    filters stored in the options.
    """
    level = getattr(suite, 'level', dlevel)
    layer = getattr(suite, 'layer', dlayer)
    if not isinstance(layer, basestring):
        layer = name_from_layer(layer)

    if isinstance(suite, unittest.TestSuite):
        for possible_suite in suite:
            for r in tests_from_suite(possible_suite, options, level, layer):
                yield r
    elif isinstance(suite, StartUpFailure):
        yield (suite, None)
    else:
        if level <= options.at_level:
            for pat in options.test:
                if pat(str(suite)):
                    yield (suite, layer)
                    break


def find_suites(options):
    for fpath, package in find_test_files(options):
        for (prefix, prefix_package) in options.prefix:
            if fpath.startswith(prefix) and package == prefix_package:
                # strip prefix, strip .py suffix and convert separator to dots
                noprefix = fpath[len(prefix):]
                noext = strip_py_ext(options, noprefix)
                assert noext is not None
                module_name = noext.replace(os.path.sep, '.')
                if package:
                    module_name = package + '.' + module_name

                for filter in options.module:
                    if filter(module_name):
                        break
                else:
                    continue

                try:
                    module = import_name(module_name)
                except KeyboardInterrupt:
                    raise
                except:
                    suite = StartUpFailure(
                        options, module_name,
                        sys.exc_info()[:2]
                        + (sys.exc_info()[2].tb_next.tb_next,),
                        )
                else:
                    try:
                        suite = getattr(module, options.suite_name)()
                        if isinstance(suite, unittest.TestSuite):
                            check_suite(suite, module_name)
                        else:
                            raise TypeError(
                                "Invalid test_suite, %r, in %s"
                                % (suite, module_name)
                                )
                    except KeyboardInterrupt:
                        raise
                    except:
                        suite = StartUpFailure(
                            options, module_name, sys.exc_info()[:2]+(None,))


                yield suite
                break


def check_suite(suite, module_name):
    """Check for bad tests in a test suite.

    "Bad tests" are those that do not inherit from unittest.TestCase.

    Note that this function is pointless on Python 2.5, because unittest itself
    checks for this in TestSuite.addTest.  It is, however, useful on earlier
    Pythons.
    """
    for x in suite:
        if isinstance(x, unittest.TestSuite):
            check_suite(x, module_name)
        elif not isinstance(x, unittest.TestCase):
            raise TypeError(
                "Invalid test, %r,\nin test_suite from %s"
                % (x, module_name)
                )




class StartUpFailure(unittest.TestCase):
    """Empty test case added to the test suite to indicate import failures."""

    def __init__(self, options, module, exc_info):
        if options.post_mortem:
            post_mortem(exc_info)
        self.module = module
        self.exc_info = exc_info


def find_test_files(options):
    found = {}
    for f, package in find_test_files_(options):
        if f not in found:
            found[f] = 1
            yield f, package

identifier = re.compile(r'[_a-zA-Z]\w*$').match
def find_test_files_(options):
    tests_pattern = options.tests_pattern
    test_file_pattern = options.test_file_pattern

    # If options.usecompiled, we can accept .pyc or .pyo files instead
    # of .py files.  We'd rather use a .py file if one exists.  `root2ext`
    # maps a test file path, sans extension, to the path with the best
    # extension found (.py if it exists, else .pyc or .pyo).
    # Note that "py" < "pyc" < "pyo", so if more than one extension is
    # found, the lexicographically smaller one is best.

    # Found a new test file, in directory `dirname`.  `noext` is the
    # file name without an extension, and `withext` is the file name
    # with its extension.
    def update_root2ext(dirname, noext, withext):
        key = os.path.join(dirname, noext)
        new = os.path.join(dirname, withext)
        if key in root2ext:
            root2ext[key] = min(root2ext[key], new)
        else:
            root2ext[key] = new

    for (p, package) in test_dirs(options, {}):
        for dirname, dirs, files in walk_with_symlinks(options, p):
            if dirname != p and not contains_init_py(options, files):
                continue    # not a plausible test directory
            root2ext = {}
            dirs[:] = filter(identifier, dirs)
            d = os.path.split(dirname)[1]
            if tests_pattern(d) and contains_init_py(options, files):
                # tests directory
                for file in files:
                    noext = strip_py_ext(options, file)
                    if noext and test_file_pattern(noext):
                        update_root2ext(dirname, noext, file)

            for file in files:
                noext = strip_py_ext(options, file)
                if noext and tests_pattern(noext):
                    update_root2ext(dirname, noext, file)

            winners = root2ext.values()
            winners.sort()
            for file in winners:
                yield file, package

def walk_with_symlinks(options, dir):
    # TODO -- really should have test of this that uses symlinks
    #         this is hard on a number of levels ...
    for dirpath, dirs, files in os.walk(dir):
        dirs.sort()
        files.sort()
        dirs[:] = [d for d in dirs if d not in options.ignore_dir]
        yield (dirpath, dirs, files)
        for d in dirs:
            p = os.path.join(dirpath, d)
            if os.path.islink(p):
                for sdirpath, sdirs, sfiles in walk_with_symlinks(options, p):
                    yield (sdirpath, sdirs, sfiles)

compiled_sufixes = '.pyc', '.pyo'
def remove_stale_bytecode(options):
    if options.keepbytecode:
        return
    for (p, _) in options.test_path:
        for dirname, dirs, files in walk_with_symlinks(options, p):
            for file in files:
                if file[-4:] in compiled_sufixes and file[:-1] not in files:
                    fullname = os.path.join(dirname, file)
                    options.output.info("Removing stale bytecode file %s"
                                        % fullname)
                    os.unlink(fullname)


def test_dirs(options, seen):
    if options.package:
        for p in options.package:
            p = import_name(p)
            for p in p.__path__:
                p = os.path.abspath(p)
                if p in seen:
                    continue
                for (prefix, package) in options.prefix:
                    if p.startswith(prefix) or p == prefix[:-1]:
                        seen[p] = 1
                        yield p, package
                        break
    else:
        for dpath in options.test_path:
            yield dpath


def import_name(name):
    __import__(name)
    return sys.modules[name]

def configure_logging():
    """Initialize the logging module."""
    import logging.config

    # Get the log.ini file from the current directory instead of
    # possibly buried in the build directory.  TODO: This isn't
    # perfect because if log.ini specifies a log file, it'll be
    # relative to the build directory.  Hmm...  logini =
    # os.path.abspath("log.ini")

    logini = os.path.abspath("log.ini")
    if os.path.exists(logini):
        logging.config.fileConfig(logini)
    else:
        # If there's no log.ini, cause the logging package to be
        # silent during testing.
        root = logging.getLogger()
        root.addHandler(NullHandler())
        logging.basicConfig()

    if os.environ.has_key("LOGGING"):
        level = int(os.environ["LOGGING"])
        logging.getLogger().setLevel(level)

class NullHandler(logging.Handler):
    """Logging handler that drops everything on the floor.

    We require silence in the test environment.  Hush.
    """

    def emit(self, record):
        pass


class TrackRefs(object):
    """Object to track reference counts across test runs."""

    def __init__(self):
        self.type2count = {}
        self.type2all = {}
        self.delta = None
        self.n = 0
        self.update()
        self.delta = None

    def update(self):
        gc.collect()
        obs = sys.getobjects(0)
        type2count = {}
        type2all = {}
        n = 0
        for o in obs:
            if type(o) is str and o == '<dummy key>':
                # avoid dictionary madness
                continue

            all = sys.getrefcount(o) - 3
            n += all

            t = type(o)
            if t is types.InstanceType:
                t = o.__class__

            if t in type2count:
                type2count[t] += 1
                type2all[t] += all
            else:
                type2count[t] = 1
                type2all[t] = all


        ct = [(
               type_or_class_title(t),
               type2count[t] - self.type2count.get(t, 0),
               type2all[t] - self.type2all.get(t, 0),
               )
              for t in type2count.iterkeys()]
        ct += [(
                type_or_class_title(t),
                - self.type2count[t],
                - self.type2all[t],
                )
               for t in self.type2count.iterkeys()
               if t not in type2count]
        ct.sort()
        self.delta = ct
        self.type2count = type2count
        self.type2all = type2all
        self.n = n


    def output(self):
        printed = False
        s1 = s2 = 0
        for t, delta1, delta2 in self.delta:
            if delta1 or delta2:
                if not printed:
                    print (
                        '    Leak details, changes in instances and refcounts'
                        ' by type/class:')
                    print "    %-55s %6s %6s" % ('type/class', 'insts', 'refs')
                    print "    %-55s %6s %6s" % ('-' * 55, '-----', '----')
                    printed = True
                print "    %-55s %6d %6d" % (t, delta1, delta2)
                s1 += delta1
                s2 += delta2

        if printed:
            print "    %-55s %6s %6s" % ('-' * 55, '-----', '----')
            print "    %-55s %6s %6s" % ('total', s1, s2)


        self.delta = None

def type_or_class_title(t):
    module = getattr(t, '__module__', '__builtin__')
    if module == '__builtin__':
        return t.__name__
    return "%s.%s" % (module, t.__name__)


###############################################################################
# Command-line UI

parser = optparse.OptionParser("Usage: %prog [options] [MODULE] [TEST]")

######################################################################
# Searching and filtering

searching = optparse.OptionGroup(parser, "Searching and filtering", """\
Options in this group are used to define which tests to run.
""")

searching.add_option(
    '--package', '--dir', '-s', action="append", dest='package',
    help="""\
Search the given package's directories for tests.  This can be
specified more than once to run tests in multiple parts of the source
tree.  For example, if refactoring interfaces, you don't want to see
the way you have broken setups for tests in other packages. You *just*
want to run the interface tests.

Packages are supplied as dotted names.  For compatibility with the old
test runner, forward and backward slashed in package names are
converted to dots.

(In the special case of packages spread over multiple directories,
only directories within the test search path are searched. See the
--path option.)

""")

searching.add_option(
    '--module', '-m', action="append", dest='module',
    help="""\
Specify a test-module filter as a regular expression.  This is a
case-sensitive regular expression, used in search (not match) mode, to
limit which test modules are searched for tests.  The regular
expressions are checked against dotted module names.  In an extension
of Python regexp notation, a leading "!" is stripped and causes the
sense of the remaining regexp to be negated (so "!bc" matches any
string that does not match "bc", and vice versa).  The option can be
specified multiple test-module filters.  Test modules matching any of
the test filters are searched.  If no test-module filter is specified,
then all test modules are used.
""")

searching.add_option(
    '--test', '-t', action="append", dest='test',
    help="""\
Specify a test filter as a regular expression.  This is a
case-sensitive regular expression, used in search (not match) mode, to
limit which tests are run.  In an extension of Python regexp notation,
a leading "!" is stripped and causes the sense of the remaining regexp
to be negated (so "!bc" matches any string that does not match "bc",
and vice versa).  The option can be specified multiple test filters.
Tests matching any of the test filters are included.  If no test
filter is specified, then all tests are run.
""")

searching.add_option(
    '--unit', '-u', action="store_true", dest='unit',
    help="""\
Run only unit tests, ignoring any layer options.
""")

searching.add_option(
    '--non-unit', '-f', action="store_true", dest='non_unit',
    help="""\
Run tests other than unit tests.
""")

searching.add_option(
    '--layer', action="append", dest='layer',
    help="""\
Specify a test layer to run.  The option can be given multiple times
to specify more than one layer.  If not specified, all layers are run.
It is common for the running script to provide default values for this
option.  Layers are specified regular expressions, used in search
mode, for dotted names of objects that define a layer.  In an
extension of Python regexp notation, a leading "!" is stripped and
causes the sense of the remaining regexp to be negated (so "!bc"
matches any string that does not match "bc", and vice versa).  The
layer named 'unit' is reserved for unit tests, however, take note of
the --unit and non-unit options.
""")

searching.add_option(
    '-a', '--at-level', type='int', dest='at_level',
    help="""\
Run the tests at the given level.  Any test at a level at or below
this is run, any test at a level above this is not run.  Level 0
runs all tests.
""")

searching.add_option(
    '--all', action="store_true", dest='all',
    help="Run tests at all levels.")

searching.add_option(
    '--list-tests', action="store_true", dest='list_tests', default=False,
    help="List all tests that matched your filters.  Do not run any tests.")

parser.add_option_group(searching)

######################################################################
# Reporting

reporting = optparse.OptionGroup(parser, "Reporting", """\
Reporting options control basic aspects of test-runner output
""")

reporting.add_option(
    '--verbose', '-v', action="count", dest='verbose',
    help="""\
Make output more verbose.
Increment the verbosity level.
""")

reporting.add_option(
    '--quiet', '-q', action="store_true", dest='quiet',
    help="""\
Make the output minimal, overriding any verbosity options.
""")

reporting.add_option(
    '--progress', '-p', action="store_true", dest='progress',
    help="""\
Output progress status
""")

reporting.add_option(
    '--no-progress',action="store_false", dest='progress',
    help="""\
Do not output progress status.  This is the default, but can be used to
counter a previous use of --progress or -p.
""")

# We use a noop callback because the actual processing will be done in the
# get_options function, but we want optparse to generate appropriate help info
# for us, so we add an option anyway.
reporting.add_option(
    '--auto-progress', action="callback", callback=lambda *args: None,
    help="""\
Output progress status, but only when stdout is a terminal.
""")

reporting.add_option(
    '--color', '-c', action="store_true", dest='color',
    help="""\
Colorize the output.
""")

reporting.add_option(
    '--no-color', '-C', action="store_false", dest='color',
    help="""\
Do not colorize the output.  This is the default, but can be used to
counter a previous use of --color or -c.
""")

# We use a noop callback because the actual processing will be done in the
# get_options function, but we want optparse to generate appropriate help info
# for us, so we add an option anyway.
reporting.add_option(
    '--auto-color', action="callback", callback=lambda *args: None,
    help="""\
Colorize the output, but only when stdout is a terminal.
""")

reporting.add_option(
    '--slow-test', type='float', dest='slow_test_threshold',
    metavar='N', default=10,
    help="""\
With -c and -vvv, highlight tests that take longer than N seconds (default:
%default).
""")

reporting.add_option(
    '-1', '--hide-secondary-failures',
    action="store_true", dest='report_only_first_failure',
    help="""\
Report only the first failure in a doctest. (Examples after the
failure are still executed, in case they do any cleanup.)
""")

reporting.add_option(
    '--show-secondary-failures',
    action="store_false", dest='report_only_first_failure',
    help="""\
Report all failures in a doctest.  This is the default, but can
be used to counter a default use of -1 or --hide-secondary-failures.
""")

reporting.add_option(
    '--ndiff', action="store_true", dest="ndiff",
    help="""\
When there is a doctest failure, show it as a diff using the ndiff.py utility.
""")

reporting.add_option(
    '--udiff', action="store_true", dest="udiff",
    help="""\
When there is a doctest failure, show it as a unified diff.
""")

reporting.add_option(
    '--cdiff', action="store_true", dest="cdiff",
    help="""\
When there is a doctest failure, show it as a context diff.
""")

parser.add_option_group(reporting)

######################################################################
# Analysis

analysis = optparse.OptionGroup(parser, "Analysis", """\
Analysis options provide tools for analysing test output.
""")


analysis.add_option(
    '--post-mortem', '-D', action="store_true", dest='post_mortem',
    help="Enable post-mortem debugging of test failures"
    )


analysis.add_option(
    '--gc', '-g', action="append", dest='gc', type="int",
    help="""\
Set the garbage collector generation threshold.  This can be used
to stress memory and gc correctness.  Some crashes are only
reproducible when the threshold is set to 1 (aggressive garbage
collection).  Do "--gc 0" to disable garbage collection altogether.

The --gc option can be used up to 3 times to specify up to 3 of the 3
Python gc_threshold settings.

""")

analysis.add_option(
    '--gc-option', '-G', action="append", dest='gc_option', type="choice",
    choices=['DEBUG_STATS', 'DEBUG_COLLECTABLE', 'DEBUG_UNCOLLECTABLE',
             'DEBUG_INSTANCES', 'DEBUG_OBJECTS', 'DEBUG_SAVEALL',
             'DEBUG_LEAK'],
    help="""\
Set a Python gc-module debug flag.  This option can be used more than
once to set multiple flags.
""")

analysis.add_option(
    '--repeat', '-N', action="store", type="int", dest='repeat',
    help="""\
Repeat the tests the given number of times.  This option is used to
make sure that tests leave their environment in the state they found
it and, with the --report-refcounts option to look for memory leaks.
""")

analysis.add_option(
    '--report-refcounts', '-r', action="store_true", dest='report_refcounts',
    help="""\
After each run of the tests, output a report summarizing changes in
refcounts by object type.  This option that requires that Python was
built with the --with-pydebug option to configure.
""")

analysis.add_option(
    '--coverage', action="store", type='string', dest='coverage',
    help="""\
Perform code-coverage analysis, saving trace data to the directory
with the given name.  A code coverage summary is printed to standard
out.
""")

analysis.add_option(
    '--profile', action="store", dest='profile', type="choice",
    choices=available_profilers.keys(),
    help="""\
Run the tests under cProfiler or hotshot and display the top 50 stats, sorted
by cumulative time and number of calls.
""")

def do_pychecker(*args):
    if not os.environ.get("PYCHECKER"):
        os.environ["PYCHECKER"] = "-q"
    import pychecker.checker

analysis.add_option(
    '--pychecker', action="callback", callback=do_pychecker,
    help="""\
Run the tests under pychecker
""")

parser.add_option_group(analysis)

######################################################################
# Setup

setup = optparse.OptionGroup(parser, "Setup", """\
Setup options are normally supplied by the testrunner script, although
they can be overridden by users.
""")

setup.add_option(
    '--path', action="append", dest='path',
    help="""\
Specify a path to be added to Python's search path.  This option can
be used multiple times to specify multiple search paths.  The path is
usually specified by the test-runner script itself, rather than by
users of the script, although it can be overridden by users.  Only
tests found in the path will be run.

This option also specifies directories to be searched for tests.
See the search_directory.
""")

setup.add_option(
    '--test-path', action="append", dest='test_path',
    help="""\
Specify a path to be searched for tests, but not added to the Python
search path.  This option can be used multiple times to specify
multiple search paths.  The path is usually specified by the
test-runner script itself, rather than by users of the script,
although it can be overridden by users.  Only tests found in the path
will be run.
""")

setup.add_option(
    '--package-path', action="append", dest='package_path', nargs=2,
    help="""\
Specify a path to be searched for tests, but not added to the Python
search path.  Also specify a package for files found in this path.
This is used to deal with directories that are stitched into packages
that are not otherwise searched for tests.

This option takes 2 arguments.  The first is a path name. The second is
the package name.

This option can be used multiple times to specify
multiple search paths.  The path is usually specified by the
test-runner script itself, rather than by users of the script,
although it can be overridden by users.  Only tests found in the path
will be run.
""")

setup.add_option(
    '--tests-pattern', action="store", dest='tests_pattern',
    help="""\
The test runner looks for modules containing tests.  It uses this
pattern to identify these modules.  The modules may be either packages
or python files.

If a test module is a package, it uses the value given by the
test-file-pattern to identify python files within the package
containing tests.
""")

setup.add_option(
    '--suite-name', action="store", dest='suite_name',
    help="""\
Specify the name of the object in each test_module that contains the
module's test suite.
""")

setup.add_option(
    '--test-file-pattern', action="store", dest='test_file_pattern',
    help="""\
Specify a pattern for identifying python files within a tests package.
See the documentation for the --tests-pattern option.
""")

setup.add_option(
    '--ignore_dir', action="append", dest='ignore_dir',
    help="""\
Specifies the name of a directory to ignore when looking for tests.
""")

parser.add_option_group(setup)

######################################################################
# Other

other = optparse.OptionGroup(parser, "Other", "Other options")

other.add_option(
    '--keepbytecode', '-k', action="store_true", dest='keepbytecode',
    help="""\
Normally, the test runner scans the test paths and the test
directories looking for and deleting pyc or pyo files without
corresponding py files.  This is to prevent spurious test failures due
to finding compiled modules where source modules have been deleted.
This scan can be time consuming.  Using this option disables this
scan.  If you know you haven't removed any modules since last running
the tests, can make the test run go much faster.
""")

other.add_option(
    '--usecompiled', action="store_true", dest='usecompiled',
    help="""\
Normally, a package must contain an __init__.py file, and only .py files
can contain test code.  When this option is specified, compiled Python
files (.pyc and .pyo) can be used instead:  a directory containing
__init__.pyc or __init__.pyo is also considered to be a package, and if
file XYZ.py contains tests but is absent while XYZ.pyc or XYZ.pyo exists
then the compiled files will be used.  This is necessary when running
tests against a tree where the .py files have been removed after
compilation to .pyc/.pyo.  Use of this option implies --keepbytecode.
""")

other.add_option(
    '--exit-with-status', action="store_true", dest='exitwithstatus',
    help="""\
Return an error exit status if the tests failed.  This can be useful for
an invoking process that wants to monitor the result of a test run.
""")

parser.add_option_group(other)

######################################################################
# Command-line processing

def compile_filter(pattern):
    if pattern.startswith('!'):
        pattern = re.compile(pattern[1:]).search
        return (lambda s: not pattern(s))
    return re.compile(pattern).search

def merge_options(options, defaults):
    odict = options.__dict__
    for name, value in defaults.__dict__.items():
        if (value is not None) and (odict[name] is None):
            odict[name] = value

default_setup_args = [
    '--tests-pattern', '^tests$',
    '--at-level', '1',
    '--ignore', '.svn',
    '--ignore', 'CVS',
    '--ignore', '{arch}',
    '--ignore', '.arch-ids',
    '--ignore', '_darcs',
    '--test-file-pattern', '^test',
    '--suite-name', 'test_suite',
    ]


def terminal_has_colors():
    """Determine whether the terminal supports colors.

    Some terminals (e.g. the emacs built-in one) don't.
    """
    return tigetnum('colors', -1) >= 8


def get_options(args=None, defaults=None):
    # Because we want to inspect stdout and decide to colorize or not, we
    # replace the --auto-color option with the appropriate --color or
    # --no-color option.  That way the subprocess doesn't have to decide (which
    # it would do incorrectly anyway because stdout would be a pipe).
    def apply_auto_color(args):
        if args and '--auto-color' in args:
            if sys.stdout.isatty() and terminal_has_colors():
                colorization = '--color'
            else:
                colorization = '--no-color'

            args[:] = [arg.replace('--auto-color', colorization)
                       for arg in args]

    # The comment of apply_auto_color applies here as well
    def apply_auto_progress(args):
        if args and '--auto-progress' in args:
            if sys.stdout.isatty():
                progress = '--progress'
            else:
                progress = '--no-progress'

            args[:] = [arg.replace('--auto-progress', progress)
                       for arg in args]

    apply_auto_color(args)
    apply_auto_color(defaults)
    apply_auto_progress(args)
    apply_auto_progress(defaults)

    default_setup, _ = parser.parse_args(default_setup_args)
    assert not _
    if defaults:
        defaults, _ = parser.parse_args(defaults)
        assert not _
        merge_options(defaults, default_setup)
    else:
        defaults = default_setup

    if args is None:
        args = sys.argv

    original_testrunner_args = args
    args = args[1:]

    options, positional = parser.parse_args(args)
    merge_options(options, defaults)
    options.original_testrunner_args = original_testrunner_args

    if options.color:
        options.output = ColorfulOutputFormatter(options)
        options.output.slow_test_threshold = options.slow_test_threshold
    else:
        options.output = OutputFormatter(options)

    options.fail = False

    if positional:
        module_filter = positional.pop(0)
        if module_filter != '.':
            if options.module:
                options.module.append(module_filter)
            else:
                options.module = [module_filter]

        if positional:
            test_filter = positional.pop(0)
            if options.test:
                options.test.append(test_filter)
            else:
                options.test = [test_filter]

            if positional:
                parser.error("Too many positional arguments")

    options.ignore_dir = dict([(d,1) for d in options.ignore_dir])
    options.test_file_pattern = re.compile(options.test_file_pattern).search
    options.tests_pattern = re.compile(options.tests_pattern).search
    options.test = map(compile_filter, options.test or ('.'))
    options.module = map(compile_filter, options.module or ('.'))

    options.path = map(os.path.abspath, options.path or ())
    options.test_path = map(os.path.abspath, options.test_path or ())
    options.test_path += options.path

    options.test_path = ([(path, '') for path in options.test_path]
                         +
                         [(os.path.abspath(path), package)
                          for (path, package) in options.package_path or ()
                          ])

    if options.package:
        # DM 2008-06-25: filter out '--test-path' values as
        #   they are not involved in package resolution
        #pkgmap = dict(options.test_path)
        pkgmap = dict([(path, '') for path in options.path]
                      + (options.package_path or [])
                      )
        options.package = [normalize_package(p, pkgmap)
                           for p in options.package]

    options.prefix = [(path + os.path.sep, package)
                      for (path, package) in options.test_path]
    if options.all:
        options.at_level = sys.maxint

    if options.unit and options.non_unit:
        # The test runner interprets this as "run only those tests that are
        # both unit and non-unit at the same time".  The user, however, wants
        # to run both unit and non-unit tests.  Disable the filtering so that
        # the user will get what she wants:
        options.unit = options.non_unit = False

    if options.unit:
        options.layer = ['unit']
    if options.layer:
        options.layer = map(compile_filter, options.layer)

    options.layer = options.layer and dict([(l, 1) for l in options.layer])

    if options.usecompiled:
        options.keepbytecode = options.usecompiled

    if options.quiet:
        options.verbose = 0

    if options.report_refcounts and options.repeat < 2:
        print """\
        You must use the --repeat (-N) option to specify a repeat
        count greater than 1 when using the --report_refcounts (-r)
        option.
        """
        options.fail = True
        return options


    if options.report_refcounts and not hasattr(sys, "gettotalrefcount"):
        print """\
        The Python you are running was not configured
        with --with-pydebug. This is required to use
        the --report-refcounts option.
        """
        options.fail = True
        return options

    return options

def normalize_package(package, package_map={}):
    r"""Normalize package name passed to the --package option.

        >>> normalize_package('zope.testing')
        'zope.testing'

    Converts path names into package names for compatibility with the old
    test runner.

        >>> normalize_package('zope/testing')
        'zope.testing'
        >>> normalize_package('zope/testing/')
        'zope.testing'
        >>> normalize_package('zope\\testing')
        'zope.testing'

    Can use a map of absolute pathnames to package names

        >>> a = os.path.abspath
        >>> normalize_package('src/zope/testing/',
        ...                   {a('src'): ''})
        'zope.testing'
        >>> normalize_package('src/zope_testing/',
        ...                   {a('src/zope_testing'): 'zope.testing'})
        'zope.testing'
        >>> normalize_package('src/zope_something/tests',
        ...                   {a('src/zope_something'): 'zope.something',
        ...                    a('src'): ''})
        'zope.something.tests'

    """
    package = package.replace('\\', '/')
    if package.endswith('/'):
        package = package[:-1]
    bits = package.split('/')
    for n in range(len(bits), 0, -1):
        pkg = package_map.get(os.path.abspath('/'.join(bits[:n])))
        if pkg is not None:
            bits = bits[n:]
            if pkg:
                bits = [pkg] + bits
            return '.'.join(bits)
    return package.replace('/', '.')

# Command-line UI
###############################################################################

###############################################################################
# Install 2.4 TestSuite __iter__ into earlier versions

if sys.version_info < (2, 4):
    def __iter__(suite):
        return iter(suite._tests)
    unittest.TestSuite.__iter__ = __iter__
    del __iter__

# Install 2.4 TestSuite __iter__ into earlier versions
###############################################################################

###############################################################################
# Test the testrunner

def test_suite():

    import renormalizing
    checker = renormalizing.RENormalizing([
        # 2.5 changed the way pdb reports exceptions
        (re.compile(r"<class 'exceptions.(\w+)Error'>:"),
                    r'exceptions.\1Error:'),

        (re.compile('^> [^\n]+->None$', re.M), '> ...->None'),
        (re.compile(r"<module>"),(r'?')),
        (re.compile(r"<type 'exceptions.(\w+)Error'>:"),
                    r'exceptions.\1Error:'),
        (re.compile("'[A-Za-z]:\\\\"), "'"), # hopefully, we'll make Windows happy
        (re.compile(r'\\\\'), '/'), # more Windows happiness
        (re.compile(r'\\'), '/'), # even more Windows happiness
        (re.compile('/r'), '\\\\r'), # undo damage from previous
        (re.compile(r'\r'), '\\\\r\n'),
        (re.compile(r'\d+[.]\d\d\d seconds'), 'N.NNN seconds'),
        (re.compile(r'\d+[.]\d\d\d s'), 'N.NNN s'),
        (re.compile(r'\d+[.]\d\d\d{'), 'N.NNN{'),
        (re.compile('( |")[^\n]+testrunner-ex'), r'\1testrunner-ex'),
        (re.compile('( |")[^\n]+testrunner.py'), r'\1testrunner.py'),
        (re.compile(r'> [^\n]*(doc|unit)test[.]py\(\d+\)'),
                    r'\1test.py(NNN)'),
        (re.compile(r'[.]py\(\d+\)'), r'.py(NNN)'),
        (re.compile(r'[.]py:\d+'), r'.py:NNN'),
        (re.compile(r' line \d+,', re.IGNORECASE), r' Line NNN,'),
        (re.compile(r' line {([a-z]+)}\d+{', re.IGNORECASE), r' Line {\1}NNN{'),

        # omit traceback entries for unittest.py or doctest.py from
        # output:
        (re.compile(r'^ +File "[^\n]*(doc|unit)test.py", [^\n]+\n[^\n]+\n',
                    re.MULTILINE),
         r''),
        (re.compile(r'^{\w+} +File "{\w+}[^\n]*(doc|unit)test.py{\w+}", [^\n]+\n[^\n]+\n',
                    re.MULTILINE),
         r''),
        (re.compile('^> [^\n]+->None$', re.M), '> ...->None'),
        (re.compile('import pdb; pdb'), 'Pdb()'), # Py 2.3
        ])

    def setUp(test):
        test.globs['saved-sys-info'] = (
            sys.path[:],
            sys.argv[:],
            sys.modules.copy(),
            gc.get_threshold(),
            os.getcwd(),
            )
        test.globs['this_directory'] = os.path.split(__file__)[0]
        test.globs['testrunner_script'] = __file__

    def tearDown(test):
        sys.path[:], sys.argv[:] = test.globs['saved-sys-info'][:2]
        gc.set_threshold(*test.globs['saved-sys-info'][3])
        sys.modules.clear()
        sys.modules.update(test.globs['saved-sys-info'][2])
        os.chdir(test.globs['saved-sys-info'][4])

    suites = [
        doctest.DocFileSuite(
        'testrunner-arguments.txt',
        'testrunner-coverage.txt',
        'testrunner-debugging-layer-setup.test',
        'testrunner-debugging.txt',
        'testrunner-edge-cases.txt',
        'testrunner-errors.txt',
        'testrunner-layers-ntd.txt',
        'testrunner-layers.txt',
        'testrunner-layers-api.txt',
        'testrunner-progress.txt',
        'testrunner-colors.txt',
        'testrunner-simple.txt',
        'testrunner-test-selection.txt',
        'testrunner-verbose.txt',
        'testrunner-wo-source.txt',
        'testrunner-repeat.txt',
        'testrunner-gc.txt',
        'testrunner-knit.txt',
        'testrunner-package-normalization.txt',
        setUp=setUp, tearDown=tearDown,
        optionflags=doctest.ELLIPSIS+doctest.NORMALIZE_WHITESPACE,
        checker=checker),
        doctest.DocTestSuite()
        ]

    if sys.platform == 'win32':
        suites.append(
            doctest.DocFileSuite(
            'testrunner-coverage-win32.txt',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.ELLIPSIS+doctest.NORMALIZE_WHITESPACE,
            checker=checker))

    # Python <= 2.4.1 had a bug that prevented hotshot from running in
    # non-optimize mode
    if sys.version_info[:3] > (2,4,1) or not __debug__:
        # some Linux distributions don't include the profiling module (which
        # hotshot.stats depends on)
        try:
            import hotshot.stats
        except ImportError:
            pass
        else:
            suites.append(
                doctest.DocFileSuite(
                    'testrunner-profiling.txt',
                    setUp=setUp, tearDown=tearDown,
                    optionflags=doctest.ELLIPSIS+doctest.NORMALIZE_WHITESPACE,
                    checker = renormalizing.RENormalizing([
                        (re.compile(r'tests_profile[.]\S*[.]prof'),
                         'tests_profile.*.prof'),
                        ]),
                    )
                )
        try:
            import cProfile
            import pstats
        except ImportError:
            pass
        else:
            suites.append(
                doctest.DocFileSuite(
                    'testrunner-profiling-cprofiler.txt',
                    setUp=setUp, tearDown=tearDown,
                    optionflags=doctest.ELLIPSIS+doctest.NORMALIZE_WHITESPACE,
                    checker = renormalizing.RENormalizing([
                        (re.compile(r'tests_profile[.]\S*[.]prof'),
                         'tests_profile.*.prof'),
                        ]),
                    )
                )


    if hasattr(sys, 'gettotalrefcount'):
        suites.append(
            doctest.DocFileSuite(
            'testrunner-leaks.txt',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.ELLIPSIS+doctest.NORMALIZE_WHITESPACE,
            checker = renormalizing.RENormalizing([
              (re.compile(r'\d+[.]\d\d\d seconds'), 'N.NNN seconds'),
              (re.compile(r'sys refcount=\d+ +change=\d+'),
               'sys refcount=NNNNNN change=NN'),
              (re.compile(r'sum detail refcount=\d+ +'),
               'sum detail refcount=NNNNNN '),
              (re.compile(r'total +\d+ +\d+'),
               'total               NNNN    NNNN'),
              (re.compile(r"^ +(int|type) +-?\d+ +-?\d+ *\n", re.M),
               ''),
              ]),

            )
        )
    else:
        suites.append(
            doctest.DocFileSuite(
            'testrunner-leaks-err.txt',
            setUp=setUp, tearDown=tearDown,
            optionflags=doctest.ELLIPSIS+doctest.NORMALIZE_WHITESPACE,
            checker=checker,
            )
        )


    return unittest.TestSuite(suites)

def main():
    default = [
        '--path', os.path.split(sys.argv[0])[0],
        '--tests-pattern', '^testrunner$',
        ]
    run(default)

if __name__ == '__main__':

    # if --resume_layer is in the arguments, we are being run from the
    # test runner's own tests.  We need to adjust the path in hopes of
    # not getting a different version installed in the system python.
    if len(sys.argv) > 1 and sys.argv[1] == '--resume-layer':
        sys.path.insert(0,
            os.path.split(
                os.path.split(
                    os.path.split(
                        os.path.abspath(sys.argv[0])
                        )[0]
                    )[0]
                )[0]
            )

    # Hm, when run as a script, we need to import the testrunner under
    # its own name, so that there's the imported flavor has the right
    # real_pdb_set_trace.
    import zope.testing.testrunner
    from zope.testing import doctest

    main()

# Test the testrunner
###############################################################################

# Delay import to give main an opportunity to fix up the path if
# necessary
from zope.testing import doctest

########################################################################
#
# File:   common.py
# Author: Alex Samuel
# Date:   2000-12-20
#
# Contents:
#   General-purpose classes and functions.
#
# Copyright (c) 2000, 2001, 2002 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

import base64
import ConfigParser
import cPickle
import cStringIO
import dircache
import gzip
import imp
import operator
import os
import os.path
import quopri
import random
import re
import socket
import string
import sys
import tempfile
import time
import traceback
import types

########################################################################
# program name
########################################################################

program_name = "??"
"""The name of the application program."""

########################################################################
# exceptions
########################################################################

class Empty:
    """An empty class."""

    pass


class QMException(Exception):
    """An exception generated directly by QM.

    All exceptions thrown by QM should be derived from this class."""
    
    pass


class MethodShouldBeOverriddenError(QMException):
    """Indicates a method was called that should have been overridden."""

    pass



class MutexError(QMException):
    """A problem occurred with a mutex."""

    pass



class MutexLockError(QMException):
    """A lock was not obtained on the mutex."""

    pass



class ConfigurationError(QMException):

    pass



class UserError(QMException):

    pass



########################################################################
# classes
########################################################################

class FileSystemMutex:
    """A mutual exclusion lock residing in the file system."""

    retry_interval = 0.1
    """The interval, in seconds, at which to retry a lock."""


    def __init__(self, path):
        "Create a new mutex at 'path'.  No lock is aquired."""

        self.__path = path
        self.__pid_filename = os.path.join(path, "pid")

        # Perform sanity check.  If 'path' exists, it should be a
        # lock held by another instance of this class.
        if os.path.exists(self.__path):
            if not os.path.isdir(self.__path):
                raise RuntimeError, "path exists and isn't a directory"

        self.__locked = 0


    def GetPath(self):
        """Return the path of the lock."""

        return self.__path


    def Lock(self, timeout=None):
        """Aquire a lock.  If the mutex is already held, block.

        'timeout' -- If 'None', the lock operation blocks
        indefinitely, until the mutex is available.  If not 'None',
        this is a timeout, in seconds, after which to give up.  If
        zero, this function returns immediately if a lock cannot be
        acquired.

        raises -- 'MutexError' if there is a problem with the mutex.

        raises -- 'MutexLockError' if a lock was not acquired."""

        # Don't allow double locks.
        if self.__locked:
            return

        start_time = time.time()
        while 1:
            parent_dir = os.path.dirname(self.__path)
            # Make sure the parent directory exists.
            if not os.path.isdir(parent_dir):
                raise MutexError, \
                      "parent directory %s doesn't exist" % parent_dir
            # Check if the directory exists.
            if not os.path.isdir(self.__path):
                # If not, attempt to create it.
                try:
                    os.mkdir(self.__path)
                    # Creation succeeded; the lock is ours.
                    self.__locked = 1
                    # Write our pid into a file in the directory.
                    pid_file = open(self.__pid_filename, "w")
                    pid_file.write("%d\n" % os.getpid())
                    pid_file.close()
                    return
                except os.error:
                    # Couldn't lock.
                    pass
            # Time out yet?
            if timeout != None \
               and (time.time() - start_time) >= timeout:
                # Timed out.  Raise an exception.
                raise MutexLockError, \
                      "lock on %s timed out" % self.__path
            # Sleep for a while before trying again.
            time.sleep(self.retry_interval)

        
    def Unlock(self):
        """Release a lock."""

        # Don't try to unlock if we're not already locked.
        if not self.__locked:
            return

        # Sanity checks.
        assert os.path.isdir(self.__path)
        assert os.path.isfile(self.__pid_filename)

        # Unlock.
        os.unlink(self.__pid_filename)
        os.rmdir(self.__path)
        self.__locked = 0


    def IsLocked(self):
        """Return true if a lock is held on the mutex."""

        return self.__locked
        
        

class MapReplacer:
    """A callable object to replace text according to a map."""

    def __init__(self, replacements):
        """Generate a function to replace text according to a map.

        'replacements' -- A mapping of replacements.  For each element,
        the key is the text to match, and the corresponding value is the
        replacements for that text."""

        # Construct a regular expression that matches any of the
        # replacements.
        keys = map(re.escape, replacements.keys())
        regex = "(" + string.join(keys, "|") + ")"
        self.__regex = re.compile(regex)
        # The replacement function.  It simply looks up the replacement text
        # in 'replacements'.
        self.__substitution = lambda match, replacements=replacements: \
                              replacements[match.group(0)]


    def __call__(self, text):
        """Perform replacements in 'text'.

        returns -- The replaced text."""

        return self.__regex.sub(self.__substitution, text)



class RcConfiguration:
    """Interface object to QM configuration files.

    Configuration files are in the format parsed by the standard
    'ConfigParser' module, namely 'win.ini'--style files."""

    user_rc_file_name = ".qmrc"
    """The name of the user configuration file."""


    def __init__(self):
        """Create a new configuration instance."""

        self.__parser = None


    def Load(self, section):
        """Load configuration.

        'section' -- The configuration section from which subsequent
        varaibles are loaded."""

        self.__parser = self.__Load()
        self.__section = section


    def Get(self, option, default, section=None):
        """Retrieve a configuration variable.

        'option' -- The name of the option to retrieve.

        'default' -- The default value to return if the option is not
        found.

        'section' -- The section from which to retrieve the option.
        'None' indicates the section specified to the 'Load' method for
        this instance.  

        precondition -- The RC configuration must be loaded."""

        if self.__parser is None:
            # No RC file was ever loaded.  Print a warning the first
            # time. 
            if not hasattr(self, "no_rc_loaded_warning"):
                sys.stderr.write("Warning: No RC configuration file loaded.\n")
                self.no_rc_loaded_warning = 1
            # Use the default.             
            return default
        
        # Use the previously-specified default section, if one wasn't
        # specified explicitly.
        if section is None:
            section = self.__section

        try:
            # Try to get the requested option.
            return self.__parser.get(section, option)
        except ConfigParser.NoSectionError:
            # Couldn't find the section.
            return default
        except ConfigParser.NoOptionError:
            # Couldn't find the option.
            return default


    def GetOptions(self, section=None):
        """Return a sequence of options.

        'section' -- The section for which to list options, or 'None'
        for the section specified to 'Load'.

        precondition -- The RC configuration must be loaded."""

        # Use the previously-specified default section, if one wasn't
        # specified explicitly.
        if section is None:
            section = self.__section
        try:
            options = self.__parser.options(section)
        except ConfigParser.NoSectionError:
            # Couldn't find the section.
            return []
        else:
            # 'ConfigParser' puts in a magic option '__name__', which is
            # the name of the section.  Remove it.
            if "__name__" in options:
                options.remove("__name__")
            return options


    def __Load(self):
        """Load the configuration from the appropriate places."""

	# Create a parser.
        parser = ConfigParser.ConfigParser()

        # Construct the path to the user's rc file.
        if os.environ.has_key("HOME"):
	        home_directory = os.environ["HOME"]
	        rc_file = os.path.join(home_directory, self.user_rc_file_name)
	        # Note that it's OK to call 'read' even if the file doesn't
		# exist.  In that, case the parser simply will not accumulate
		# any data.
	        parser.read(rc_file)
	else:	
		# If we cannot find the user's home directory, do not
		# even try to read the configuration.
		pass

        return parser



class OrderedMap:
    """A map that preserves the order of elements inserted into it.

    An 'OrderedMap' object behaves in many ways like a map.

      - It supports efficient lookup of value by key.

      - It supports 'keys' and 'values' operations efficiently.  Both
        these lists present their elements in the order they were
        inserted into the map.

      - It does not support the 'items' operation.

      - It takes more space than an ordinary map.

      - It does not support deleting of elements.  The value of an
        exisiting key may be replaced efficiently, though; this does not
        change the position of the key in the order.
    """

    # The '__keys' and '__values' lists store keys and values at
    # corresponding indices.  The '__key_map' map associates keys with
    # indices in these two lists.

    def __init__(self):
        self.__keys = []
        self.__values = []
        self.__key_map = {}


    def __getitem__(self, key):
        return self.__values[self.__key_map[key]]


    def __setitem__(self, key, value):
        try:
            index = self.__key_map[key]
        except KeyError:
            index = len(self.__keys)
            self.__keys.append(key)
            self.__values.append(value)
            self.__key_map[key] = index
        else:
            self.__values[index] = value


    def __len__(self):
        return len(self.__keys)
    

    def has_key(self, key):
        return self.__key_map.has_key(key)


    def keys(self):
        return self.__keys


    def values(self):
        return self.__values


    def get(self, key, default=None):
        try:
            index = self.__key_map[key]
        except KeyError:
            return default
        else:
            return self.__values[index]


    def clear(self):
        self.__keys = []
        self.__values = []
        self.__key_map.clear()


    def copy(self):
        result = OrderedMap()
        result.__keys = self.__keys[:]
        result.__values = self.__values[:]
        result.__key_map = self.__key_map.copy()
        return result


    def update(self, map):
        for key, value in map.items():
            self[key] = value
            

    def __str__(self):
        pairs = map(lambda i, k=self.__keys, v=self.__values: 
                        repr(k[i]) + ": " + repr(v[i]),
                    range(0, len(self.__keys)))
        return "OrderedMap{%s}" % string.join(pairs, ", ")


    def AsMap(self):
        """Return an ordinary map object."""

        result = {}
        for i in range(0, len(self.__keys)):
            result[self.__keys[i]] = self.__values[i]
        return result



########################################################################
# functions
########################################################################

def get_lib_directory(*components):
    """Return the absolute path to the top QM Python directory."""

    path = os.environ["QM_LIB_PATH"]
    return apply(os.path.join, (path, ) + components)


def get_share_directory(*components):
    """Return the path to the directory containing QM data files."""

    path = os.environ["QM_SHARE_PATH"]
    return apply(os.path.join, (path, ) + components)


def get_doc_directory(*components):
    """Return the path to the directory containing QM documentation files."""

    path = os.environ["QM_DOC_PATH"]
    return apply(os.path.join, (path, ) + components)


def format_exception(exc_info):
    """Format an exception as structured text.

    'exc_info' -- A three-element tuple containing exception info, of
    the form '(type, value, traceback)'.

    returns -- A string containing a the formatted exception."""

    # Break up the exection info tuple.
    type, value, trace = exc_info
    # Generate output.
    traceback_listing = format_traceback(exc_info)
    return "Exception '%s' : '%s'\n\n%s\n" % (type, value, traceback_listing)


def format_traceback(exc_info):
    """Format an exception traceback as structured text.
    
    'exc_info' -- A three-element tuple containing exception info, of
    the form '(type, value, traceback)'.

    returns -- A string containing a the formatted traceback."""

    return string.join(traceback.format_tb(exc_info[2]))


def format_byte_count(bytes):
    """Return the traditional representation of 'bytes' bytes."""

    kb = 1024.0
    mb = kb * 1024
    gb = mb * 1024
    tb = gb * 1024
    
    for name, order in [
        ("TB", tb),
        ("GB", gb),
        ("MB", mb),
        ("KB", kb),
        ]:
        if bytes >= order:
            return "%.1f %s" % (bytes / order, name)

    return "%d bytes" % bytes


def rmdir_recursively(path):
    """Remove the directory at 'path' and everything under it."""

    # Remove everything in the directory.
    for entry in dircache.listdir(path):
        entry_path = os.path.join(path, entry)
        if os.path.isdir(entry_path):
            rmdir_recursively(entry_path)
        else:
            os.unlink(entry_path)
    # Remove the directory itself.
    os.rmdir(path)


def replace_by_map(text, replacements):
    """Perform multiple replacements.

    'text' -- The text in which to make the replacements.

    'replacements' -- A mapping of replacements.  For each element, the
    key is the text to match, and the corresponding value is the
    replacements for that text.

    returns -- The replaced text."""

    return MapReplacer(replacements)(text)


def invert_map(m):
    """Return the inverse of 'm'.

    'm' -- A map object.

    returns -- A map of values of 'm' to corresponding keys.  If a value
    of 'm' is associated with more than one key, it is mapped to one of
    these keys in the result, but which one is undefined."""

    result = {}
    for key, value in m.items():
        result[value] = key
    return result


def convert_from_dos_text(text):
    """Replace CRLF with LF in 'text'."""

    return string.replace(text, "\r\n", "\n")


def load_module(name, path=sys.path):
    """Load a Python module.

    'name' -- The fully-qualified name of the module to load, for
    instance 'package.subpackage.module'.

    'path' -- A sequence of directory paths in which to search for the
    module, analogous to 'PYTHONPATH'.

    returns -- A module object.

    raises -- 'ImportError' if the module cannot be found."""

    # The implementation of this function follows the prescription in
    # the documentation for the standard Python 'imp' module.  See also
    # the 'knee' package included unofficially in the standard Python
    # library. 

    # Is the module already loaded?
    try:
        module = sys.modules[name]
        # It's listed; is there a module instance there?
        if module is not None:
            return module
        # Nope; go on loading.
    except KeyError:
        # No; that's OK.
        pass

    # The module may be in a package.  Split the module path into
    # components. 
    components = string.split(name, ".")
    if len(components) > 1:
        # The module is in a package.  Construct the name of the
        # containing package.
        parent_package = string.join(components[:-1], ".")
        # Load the containing package.
        package = load_module(parent_package, path)
        # Look for the module in the parent package.
        path = package.__path__
    else:
        # No containing package.
        package = None
    # The name of the module itself is the last component of the module
    # path.  
    module_name = components[-1]
    # Locate the module.
    file, file_name, description = imp.find_module(module_name, path)
    # Find the module.
    try:
        # While loading the module, add 'path' to Python's module path,
        # so that if the module references other modules, e.g. in the
        # same directory, Python can find them.  But remember the old
        # path so we can restore it afterwards.
        old_python_path = sys.path[:]
        sys.path = sys.path + path
        # Load the module.
        module = imp.load_module(name, file, file_name, description)
        # Restore the old path.
        sys.path = old_python_path
        # Loaded successfully.  If it's contained in a package, put it
        # into that package's name space.
        if package is not None:
            setattr(package, module_name, module)
        return module
    finally:
        # Close the module file, if one was opened.
        if file is not None:
            file.close()
        
        
def load_class(name, path=sys.path):
    """Load a Python class.

    'name' -- The fully-qualified (including package and module names)
    class name, for instance 'package.subpackage.module.MyClass'.  The
    class must be at the top level of the module's namespace, i.e. not
    nested in another class.

    'path' -- A sequence of directory paths in which to search for the
    containing module, analogous to 'sys.path'.

    returns -- A class object.

    raises -- 'ImportError' if the module containing the class can't be
    imported, or if there is no class with the specified name in that
    module, or if 'name' doesn't correspond to a class."""

    # Make sure the class name is fully-qualified.  It must at least be
    # in a top-level module, so there should be at least one module path
    # separator. 
    if not "." in name:
        raise QMException, \
              "%s is not a fully-qualified class name" % name
    # Split the module path into components.
    components = string.split(name, ".")
    # Reconstruct the full path to the containing module.
    module_name = string.join(components[:-1], ".")
    # The last element is the name of the class.
    class_name = components[-1]
    # Load the containing module.
    module = load_module(module_name, path)
    # Exctract the requested class.
    try:
        klass = module.__dict__[class_name]
        if not isinstance(klass, types.ClassType):
            # There's something by that name, but it's not a class
            raise QMException, "%s is not a class" % name
        return klass
    except KeyError:
        # There's no class with the requested name.
        raise QMException, \
              "no class named %s in module %s" % (class_name, module_name)
    
    
def split_path_fully(path):
    """Split 'path' into components.

    Uses 'os.path.split' recursively on the directory components of
    'path' to separate all path components.

    'path' -- The path to split.

    returns -- A list of path componets."""

    dir, entry = os.path.split(path)
    if dir == "" or dir == os.sep:
        return [ entry ]
    else:
        return split_path_fully(dir) + [ entry ]


def encode_data_as_text(data, mime_type="application/octet-stream"):
    """Encode data as text.

    'data' -- The data to encode.

    'mime_type' -- The MIME type of the data.

    returns -- A pair.  The first element designates the encoding scheme
    used.  The second is a string containing the encoded data."""

    base_type = string.split(mime_type, "/", 1)[0]

    # For the text base MIME type, use a quoted-printable encoding.
    # This makes the encoded data more human-friendly.
    if base_type == "text":
        encoding = "quoted-printable"
        input_file = cStringIO.StringIO(data)
        output_file = cStringIO.StringIO()
        quopri.encode(input_file, output_file, 0)
        data = output_file.getvalue()

    # For everything else, gzip the data and then base64-encode it.
    else:
        encoding = "gzipped base64"
        data = gzip.zlib.compress(data)
        data = base64.encodestring(data)

    return (encoding, data)


def decode_data_from_text(data, encoding):
    """Decode data that was encoded as text.

    'data' -- The encoded data.

    'encoding' -- The encoding scheme used to encode this data.

    returns -- A string containing the decoded data."""

    if encoding == "none":
        return data

    elif encoding == "quoted-printable":
        # Decode quoted-printable text.
        input_file = cStringIO.StringIO(data)
        output_file = cStringIO.StringIO()
        quopri.decode(input_file, output_file)
        return output_file.getvalue()
        
    elif encoding == "gzipped base64":
        # First base64-decode the data.
        data = base64.decodestring(data)
        # Now uncompress it.
        return gzip.zlib.decompress(data)

    else:
        # Unknown encoding type.
        raise ValueError, "unknown encoding %s" % encoding


def open_temporary_file_fd():
    """Create and open a temporary file.

    The file is open for reading and writing.  The caller is responsible
    for deleting the file when finished with it.

    returns -- A pair '(file_name, file_descriptor)' for the temporary
    file."""

    # FIXME: Security.

    file_name = tempfile.mktemp()
    try:
        # Attempt to open the file.
        fd = os.open(file_name,
                     os.O_CREAT | os.O_EXCL | os.O_RDWR,
                     0600)
    except:
        exc_info = sys.exc_info()
        raise RuntimeError, qm.error("temp file error",
                                     file_name=file_name,
                                     exc_class=str(exc_info[0]),
                                     exc_arg=str(exc_info[1]))
    return (file_name, fd)


def open_temporary_file():
    """Create and open a temporary file.

    Like 'open_temporary_file_fd', except that the second element of the
    return value is a file object."""

    file_name, fd = open_temporary_file_fd()
    return (file_name, os.fdopen(fd, "w+b"))


def make_temporary_directory():
    """Create a temporary directory.

    returns -- The path to the temporary directory."""

    dir_path = tempfile.mktemp()
    try:
        os.mkdir(dir_path, 0700)
    except:
        exc_info = sys.exc_info()
        raise RuntimeError, qm.error("temp dir error",
                                     dir_path=dir_path,
                                     exc_class=str(exc_info[0]),
                                     exc_arg=str(exc_info[1]))
    return dir_path


def find_program_in_path(program_name, path=None):
    """Attempt to locate a program in an execution path.

    'program_name' -- The name of the program to run.

    'path' -- A string encoding a list of directories (in a
    system-specifiec form) in which to look for the program.  If
    'None', the 'PATH' environment variable is used.

    returns -- The path to the program, or 'None' if it was not
    found."""

    # If no path was specified, use the PATH environment variable.
    if path is None:
        path = os.environ["PATH"]
    # Split the path into directories.
    path_separator = os.pathsep
    directories = string.split(path, path_separator)
    # Loop over directories.
    for directory in directories:
        program_path = os.path.join(directory, program_name)
        # Is there such a file, and is it executable?
        if is_executable(program_path):
            # Good -- that's the result.
            return program_path
    # Couldn't find it.
    return None


def is_executable(path):
    """Return true if 'path' is an executable file."""

    # Make sure 'path' exists.
    if not os.path.isfile(path):
        return 0
    # If we have 'os.access' available, check for executability.
    if hasattr(os, "access") and not os.access(path, os.X_OK):
        return 0
    # Looks OK.
    return 1


def starts_with(text, prefix):
    """Return true if 'prefix' is a prefix of 'text'."""

    return text[:len(prefix)] == prefix


def ends_with(text, suffix):
    """Return true if 'suffix' is a suffix of 'text'."""

    return text[-len(suffix):] == suffix


def add_exit_function(exit_function):
    """Register 'exit_function' to be called when the program exits.

    'exit_function' -- A callable that takes no arguments."""

    # Add the exit function to the list of things to do at exit.
    _exit_functions.append(exit_function)


def exit(code):
    """Exit the program.

    'code' -- The exit code to return."""

    global _exit_functions
    
    # First run exit functions.
    map(lambda fn: fn(), _exit_functions)
    # Exit.
    sys.exit(code)
    

def copy(object):
    """Make a best-effort attempt to copy 'object'.

    returns -- A copy of 'object', if feasible, or otherwise
    'object'."""

    if type(object) is types.ListType:
        # Copy lists.
        return object[:]
    elif type(object) is types.DictionaryType:
        # Copy dictionaries.
        return object.copy()
    elif type(object) is types.InstanceType:
        # For objects, look for a method named 'copy'.  If there is one,
        # call it.  Otherwise, just return the object.
        copy_function = getattr(object, "copy", None)
        if callable(copy_function):
            return object.copy()
        else:
            return object
    else:
        # Give up.
        return object


def indent_lines(text, indent):
    """Indent each line of 'text' by 'indent' spaces."""

    indentation = ' ' * indent
    # Break into lines.
    lines = string.split(text, "\n")
    # Indent each.
    lines = map(lambda line, ind=indentation: ind + line, lines)
    # Rejoin.
    return string.join(lines, "\n")


def wrap_lines(text, columns=72, break_delimiter="\\", indent=""):
    """Wrap lines in 'text' to 'columns' columns.

    'text' -- The text to wrap.

    'columns' -- The maximum number of columns of text.

    'break_delimiter' -- Text to place at the end of each broken line
    (may be an empty string).

    'indent' -- Text to place at the start of each line.  The length of
    'indent' does not count towards 'columns'.

    returns -- The wrapped text."""

    # Break into lines.
    lines = string.split(text, "\n")
    # The length into which to break lines, leaving room for the
    # delimiter. 
    new_length = columns - len(break_delimiter)
    # Loop over lines.
    for index in range(0, len(lines)):
        line = lines[index]
        # Too long?
        if len(line) > columns:
            # Yes.  How many times will we have to break it?
            breaks = len(line) / new_length
            new_line = ""
            # Construct the new line, disassembling the old as we go.
            while breaks > 0:
                new_line = new_line \
                           + line[:new_length] \
                           + break_delimiter \
                           + "\n" + indent
                line = line[new_length:]
                breaks = breaks - 1
            new_line = new_line + line
            # Replace the old line with the new.
            lines[index] = new_line
    # Indent each line.
    lines = map(lambda l, i=indent: i + l, lines)
    # Rejoin lines.
    return string.join(lines, "\n")


def print_message(min_verbose, text):
    """Print a status message, if the verbose level is high enough.

    'min_verbose' -- The minimum verbose level for which this message
    will be printed.  A message with minimum verbose level of zero is
    always printed; such messages should be used only in exceptional
    situations, and certainly never in situations likely to be "batch
    mode" use cases.

    'text' -- The text of the message."""

    if verbose >= min_verbose:
        sys.stdout.write(text)
        sys.stdout.flush()


def format_time(time_secs, local_time_zone=1):
    """Generate a text format representing a date and time.

    The output is in the format "YYYY-MM-DD HH:MM ZZZ".

    'time_secs' -- The number of seconds since the start of the UNIX
    epoch, UTC.

    'local_time_zone' -- If true, format the time in the local time
    zone.  Otherwise, format it as UTC."""

    # Convert the time in seconds to a Python time 9-tuple.
    if local_time_zone:
        time_tuple = time.localtime(time_secs)
        time_zone = time.tzname[time_tuple[8]]
    else:
        time_tuple = time.gmtime(time_secs)
        time_zone = "UTC"
    # Unpack the tuple.
    year, month, day, hour, minute, second, weekday, julian_day, \
          dst_flag = time_tuple
    # Generate the format.
    return "%(year)4d-%(month)02d-%(day)02d " \
           "%(hour)02d:%(minute)02d %(time_zone)s" % locals()


def shuffle(items, generator=None):
    """Randomize the order of elements in place.

    'items' -- A list, or other mutable sequence.

    'generator' -- The random number generator, implementing Python's
    random number generator, to use.  If 'None', use the Python 'random'
    module. 

    The elements of 'items' are rearranged randomly."""

    if generator is None:
        generator = random

    length = len(items)
    # For each element in 'items', swap the element with a
    # randomly-chosen element that appears after it.
    for i in range(0, length - 3):
        j = generator.randint(i + 1, length - 1)
        swap = items[j]
        items[j] = items[i]
        items[i] = swap


def sequence_difference(seq1, seq2):
    """Returns a sequence of items in 'seq1' but not in 'seq2'.

    'seq1', 'seq2' -- Sequences."""

    result = []
    for item in seq1:
        if item not in seq2:
            result.append(item)
    return result


def make_map_from_list(list, key_function=str):
    """Construct a map from a list.

    Each element in 'list' is added to the map.  'key_function' is
    invoked on each element to construct its key; the value is the
    element itself.  If more than one element produces a given key, the
    last one will appear under that key; the others will not appear."""

    map = {}
    for element in list:
        map[key_function(element)] = element
    return map


def purge_keys(map, keys):
    """Remove each entry from 'map' that matches a key in 'keys'.

    'map' -- A map object.

    'keys' -- A sequence of keys."""

    for key in keys:
        if map.has_key(key):
            del map[key]


def make_unique_tag():
    """Return a unique tag string."""

    global _unique_tag
    
    tag = "%d_%d" % (_unique_tag, os.getpid())
    _unique_tag = _unique_tag + 1
    return tag


def split_argument_list(command):
    """Split a command into an argument list.

    'command' -- A string containing a shell or similar command.

    returns -- An argument list obtained by splitting the command."""

    # Strip leading and trailing whitespace.
    command = string.strip(command)
    # Split the command into argument list elements at spaces.
    argument_list = re.split(" +", command)
    return argument_list


# No 'time.strptime' on non-UNIX systems, so use this instead.  This
# version is more forgiving, anyway, and uses our standardized timestamp
# format. 

def parse_time(time_string, default_local_time_zone=1):
    """Parse a date and/or time string.

    'time_string' -- A string representing a date and time in the format
    returned by 'format_time'.  This function makes a best-effort
    attempt to parse incomplete strings as well.

    'default_local_time_zone' -- If the time zone is not specified in
    'time_string' and this parameter is true, assume the time is in the
    local time zone.  If this parameter is false, assume the time is
    UTC.

    returns -- An integer number of seconds since the start of the UNIX
    epoch, UTC.

    Only UTC and the current local time zone may be specified explicitly
    in 'time_string'."""

    # Sanitize.
    time_string = string.strip(time_string)
    time_string = re.sub(" +", " ", time_string)
    time_string = re.sub("/", "-", time_string)
    # On Windows, "UTC" is spelled "GMT Standard Time".  Change that
    # to "UTC" so that we can process it with the same code we use 
    # for UNIX.
    time_string = re.sub("GMT Standard Time", "UTC", time_string)
    # Break it apart.
    components = string.split(time_string, " ")

    # Do we have a time zone at the end?
    if components[-1] == "UTC":
        # It's explicitly UTC. 
        utc = 1
        dst = 0
        components.pop()
    elif components[-1] == time.tzname[0]:
        # It's explicitly our local non-DST time zone.
        utc = 0
        dst = 0
        components.pop()
    elif time.daylight and components[-1] == time.tzname[1]:
        # It's explicitly our local DST time zone.
        utc = 0
        dst = 1
        components.pop()
    else:
        # No explicit time zone.  Use the specified default.
        if default_local_time_zone:
            utc = 0
            dst = -1
        else:
            utc = 1
            dst = 0

    # Start with the current time, in the appropriate format.
    if utc:
        time_tuple = time.gmtime(time.time())
    else:
        time_tuple = time.localtime(time.time())
    # Unpack the date tuple.
    year, month, day = time_tuple[:3]
    # Assume midnight.
    hour = 0
    minute = 0

    # Look at each part of the date/time.
    for component in components:
        if string.count(component, "-") == 2:
            # Looks like a date.
            year, month, day = map(int, string.split(component, "-"))
        elif string.count(component, ":") in [1, 2]:
            # Looks like a time.
            hour, minute = map(int, string.split(component, ":")[:2])
        else:
            # Don't understand it.
            raise ValueError
        
    # Construct a Python time tuple.
    time_tuple = (year, month, day, hour, minute, 0, 0, 0, dst)
    # Convert it to seconds.
    if utc:
        return int(timegm(time_tuple))
    else:
        return int(time.mktime(time_tuple))
    

import calendar

if "timegm" in dir(calendar):
    # Use timegm from the Python library.
    from calendar import timegm

else:
    # Note: This function can be removed if we migrate permanently to a
    # newer Python version which includes 'timegm'.

    # This function is borrowed from the Python 1.6.1 distribution's
    # 'calendar' module.  According to the Python 1.5.2 library
    # documentation, it should be present in that version too, but it's
    # not.
    def timegm(tuple):
        from calendar import *
        EPOCH = 1970
        year, month, day, hour, minute, second = tuple[:6]
        assert year >= EPOCH
        assert 1 <= month <= 12
        days = 365*(year-EPOCH) + leapdays(EPOCH, year)
        for i in range(1, month):
            days = days + mdays[i]
        if month > 2 and isleap(year):
            days = days + 1
        days = days + day - 1
        hours = days*24 + hour
        minutes = hours*60 + minute
        seconds = minutes*60 + second
        return seconds


def parse_assignment(assignment):
    """Parse an 'assignment' of the form 'name=value'.

    'aassignment' -- A string.  The string should have the form
    'name=value'.

    returns -- A pair '(name, value)'."""

    # Parse the assignment.
    try:
        (name, value) = string.split(assignment, "=", 1)
        return (name, value)
    except:
        raise QMException, \
              qm.error("invalid keyword assignment",
                       argument=assignment)


def read_assignments(file):
    """Read assignments from a 'file'.

    'file' -- A file object containing the context.  When the file is
    read, leading and trailing whitespace is discarded from each line
    in the file.  Then, lines that begin with a '#' and lines that
    contain no characters are discarded.  All other lines must be of
    the form 'NAME=VALUE' and indicate an assignment to the context
    variable 'NAME' of the indicated 'VALUE'.

    returns -- A dictionary mapping each of the indicated 'NAME's to its
    corresponding 'VALUE'.  If multiple assignments to the same 'NAME'
    are present, only the 'VALUE' from the last assignment is stored."""

    # Create an empty dictionary.
    assignments = {}
    
    # Read all the lines in the file.
    lines = file.readlines()
    # Strip out leading and trailing whitespace.
    lines = map(string.strip, lines)
    # Drop any lines that are completely blank or lines that are
    # comments.
    lines = filter(lambda x: x != "" and not starts_with(x, "#"),
                   lines)
    # Go through each of the lines to process the context assignment.
    for line in lines:
        # Parse the assignment.
        (name, value) = parse_assignment(line)
        # Add it to the context.
        assignments[name] = value

    return assignments

########################################################################
# variables
########################################################################

verbose = 0
"""The verbosity level.  Higher values specify more output."""

rc = RcConfiguration()
"""The configuration stored in system and user rc files."""

# Functions that should be called when the program exits.  Each element
# is a callable that takes no arguments.  The return value is ignored.
_exit_functions = []

# Foreign exit functions that were installed in 'sys.exitfunc' by non-QM
# code.  These should be called after the QM-installed exit functions
# are processed.
_foreign_exit_functions = []

# The next number to be used when handing out unqiue tag strings.
_unique_tag = 0

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

########################################################################
#
# File:   common.py
# Author: Alex Samuel
# Date:   2000-12-20
#
# Contents:
#   General-purpose classes and functions.
#
# Copyright (c) 2000, 2001, 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# imports
########################################################################

import base64
from   calendar import timegm
import ConfigParser
import cPickle
import cStringIO
import dircache
import gzip
import imp
import lock
import operator
import os
import os.path
import qm
import quopri
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

program_name = None
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

    def __init__(self, message):
        """Construct a new 'QMException'.

        'message' -- A string describing the cause of the message as
        structured text.  If this exception is not handled, the
        'message' will be displayed as an error message."""

        Exception.__init__(self, message)



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



class PythonException(QMException):
    """A 'PythonException' is a wrapper around a Python exception.

    A 'PythonException' is a 'QMException' and, as such, can be
    processed by the QM error-handling routines.  However, the raw
    Python exception which triggered this exception can be obtained by
    using the 'exc_type' and 'exc_value' attributes of this
    exception."""

    def __init__(self, message, exc_type, exc_value):
        """Construct a new 'PythonException'.

        'message' -- A string describing the cause of the message as
        structured text.  If this exception is not handled, the
        'message' will be displayed as an error message.

        'exc_type' -- The type of the Python exception.

        'exc_value' -- The value of the Python exception."""
        
        QMException.__init__(self, message)

        self.exc_type = exc_type
        self.exc_value = exc_value
    
########################################################################
# classes
########################################################################

class RcConfiguration(ConfigParser.ConfigParser):
    """Interface object to QM configuration files.

    Configuration files are in the format parsed by the standard
    'ConfigParser' module, namely 'win.ini'--style files."""

    user_rc_file_name = ".qmrc"
    """The name of the user configuration file."""


    def __init__(self):
        """Create a new configuration instance."""

        ConfigParser.ConfigParser.__init__(self)
        if os.environ.has_key("HOME"):
            home_directory = os.environ["HOME"]
            rc_file = os.path.join(home_directory, self.user_rc_file_name)
            # Note that it's OK to call 'read' even if the file doesn't
            # exist.  In that, case the parser simply will not
            # accumulate any data.
            self.read(rc_file)


    def Load(self, section):
        """Load configuration.

        'section' -- The configuration section from which subsequent
        variables are loaded."""

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

        # Use the previously-specified default section, if one wasn't
        # specified explicitly.
        if section is None:
            section = self.__section

        try:
            # Try to get the requested option.
            return self.get(section, option)
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
            options = self.options(section)
        except ConfigParser.NoSectionError:
            # Couldn't find the section.
            return []
        else:
            # 'ConfigParser' puts in a magic option '__name__', which is
            # the name of the section.  Remove it.
            if "__name__" in options:
                options.remove("__name__")
            return options

    
########################################################################
# functions
########################################################################

def get_share_directory(*components):
    """Return the path to a file in the QM data file directory."""

    return os.path.join(qm.prefix, qm.data_dir, *components)


def get_doc_directory(*components):
    """Return a path to a file in the QM documentation file directory."""

    if not is_installed:
        return os.path.join(qm.prefix, "qm", *components)
    else:
        return os.path.join(get_share_directory("doc"), *components)


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

    return string.join(traceback.format_tb(exc_info[2]), "\n")


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


def convert_from_dos_text(text):
    """Replace CRLF with LF in 'text'."""

    return string.replace(text, "\r\n", "\n")

__load_module_lock = lock.RLock()
"""A lock used by load_module."""

def load_module(name, search_path=sys.path, load_path=sys.path):
    """Load a Python module.

    'name' -- The fully-qualified name of the module to load, for
    instance 'package.subpackage.module'.

    'search_path' -- A sequence of directories.  These directories are
    searched to find the module.

    'load_path' -- The setting of 'sys.path' when the module is loaded.
    
    returns -- A module object.

    raises -- 'ImportError' if the module cannot be found."""

    # The implementation of this function follows the prescription in
    # the documentation for the standard Python 'imp' module.  See also
    # the 'knee' package included unofficially in the standard Python
    # library. 

    # In order to avoid getting incomplete modules, grab a lock here.
    # Use a recursive lock so that deadlock does not occur if the loaded
    # module loads more modules.
    __load_module_lock.acquire()
    try:
        # Is the module already loaded?
        module = sys.modules.get(name)
        if module:
            return module

        # The module may be in a package.  Split the module path into
        # components. 
        components = string.split(name, ".")
        if len(components) > 1:
            # The module is in a package.  Construct the name of the
            # containing package.
            parent_package = string.join(components[:-1], ".")
            # Load the containing package.
            package = load_module(parent_package, search_path, load_path)
            # Look for the module in the parent package.
            search_path = package.__path__
        else:
            # No containing package.
            package = None
        # The name of the module itself is the last component of the module
        # path.  
        module_name = components[-1]
        # Locate the module.
        file, file_name, description = imp.find_module(module_name,
                                                       search_path)
        # Find the module.
        try:
            # While loading the module, add 'path' to Python's module path,
            # so that if the module references other modules, e.g. in the
            # same directory, Python can find them.  But remember the old
            # path so we can restore it afterwards.
            old_python_path = sys.path[:]
            sys.path = load_path + sys.path
            # Load the module.
            try:
                module = imp.load_module(name, file, file_name, description)
            except:
                # Don't leave a broken module object in sys.modules.
                if sys.modules.has_key(name):
                    del sys.modules[name]
                raise
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
    finally:
        # Release the lock.
        __load_module_lock.release()

        
def load_class(name, search_path = sys.path, load_path = sys.path):
    """Load a Python class.

    'name' -- The fully-qualified (including package and module names)
    class name, for instance 'package.subpackage.module.MyClass'.  The
    class must be at the top level of the module's namespace, i.e. not
    nested in another class.

    'search_path' -- A sequence of directories.  These directories are
    searched to find the module.

    'load_path' -- The setting of 'sys.path' when the module is loaded.

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
    module = load_module(module_name, search_path, load_path)
    # Extract the requested class.
    try:
        klass = module.__dict__[class_name]
        # Check to see the KLASS really is a class.  Python 2.2's
        # "new-style" classes are not instances of types.ClassType so we
        # must check two conditions: one for old-style and one for
        # new-style classes.
        if (not isinstance(klass, types.ClassType)
            and not issubclass(klass, object)):
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

    file_name = tempfile.mktemp()
    try:
        # Attempt to open the file.
        fd = os.open(file_name,
                     os.O_CREAT | os.O_EXCL | os.O_RDWR,
                     0600)
    except:
        exc_info = sys.exc_info()
        raise QMException, \
              qm.error("temp file error",
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


def format_time_iso(time_secs):
    """Generate a ISO8601-compliant formatted date and time.

    The output is in the format "YYYY-MM-DDThh:mm:ss+TZ", where TZ is
    a timezone specifier.  We always normalize to UTC (and hence
    always use the special timezone specifier "Z"), to get proper
    sorting behaviour.

    'time_secs' -- The time to be formatted, as returned by
    e.g. 'time.time()'.

    returns -- The formatted time as a string."""

    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time_secs))


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
    lines = filter(lambda x: x != "" and not x.startswith("#"),
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

is_installed = 1
"""True if this application has been installed.

True if the application has been installed.  False if the application is
running out of the source tree."""

rc = RcConfiguration()
"""The configuration stored in system and user rc files."""

# The next number to be used when handing out unqiue tag strings.
_unique_tag = 0

# The string types available in this implementation of Python.
try:
    string_types = (types.StringType, types.UnicodeType)
except AttributeError:
    string_types = (types.StringType,)

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

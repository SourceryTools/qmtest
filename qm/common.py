########################################################################
#
# File:   common.py
# Author: Alex Samuel
# Date:   2000-12-20
#
# Contents:
#   General-purpose classes and functions.
#
# Copyright (c) 2000 by CodeSourcery, LLC.  All rights reserved. 
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
########################################################################

########################################################################
# imports
########################################################################

import base64
import ConfigParser
import cPickle
import cStringIO
import gzip
import imp
import os
import os.path
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

program_name = "??"
"""The name of the application program."""

########################################################################
# exceptions
########################################################################

class MethodShouldBeOverriddenError(Exception):
    """Indicates a method was called that should have been overridden."""

    pass



class MutexLockError(Exception):
    """Indicates that a file exists that wasn't expected to."""

    pass



class ConfigurationError(RuntimeError):

    pass



class UserError(Exception):

    pass



########################################################################
# classes
########################################################################

class Enumeral:
    """A value in an enumeration.

    An enumeral represents one value of an enumeration, a one-to-one
    mapping between string names and values.  Either the string or
    numerical value may be used."""

    def __init__(self, enumeration, value):
        """Create a new enumeral.

        'enumeration' -- A mapping from names to values representing the
        enumeration of which this enumeral is a value.

        'value' -- The enumeral value.  Must be a member of
        'enumeration'."""

        self.__enumeration = enumeration
        self.__Set(value)


    def __repr__(self):
        return "<enumral %s %d>" % (self.__GetName(), self.__value)


    def __str__(self):
        return self.__GetName()


    def __cmp__(self, other):
        try:
            other_as_int = int(other)
        except ValueError:
            return cmp(self.__GetName(), other)
        else:
            return cmp(self.__value, other_as_int)


    def __hash__(self):
        return hash(self.__value)


    def __nonzero__(self):
        return 1


    def __int__(self):
        return self.__value


    def GetEnumeration(self):
        """Return a map of the enumeration of which this is a value."""

        return self.__enumeration


    # Helper methods.

    def __GetName(self):
        """Return the string representation."""

        for name, value in self.__enumeration.items():
            if value == self.__value:
                return name


    def __Set(self, value):
        """Set the enumeral value.

        'value' -- Either a string or an integer, represeting a value in
        the enumeration."""

        try:
            self.__value = self.__enumeration[value]
        except KeyError:
            if value in self.__enumeration.values():
                self.__value = value
            else:
                raise ValueError, "invalid enumeral value: %s" % repr(value)



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

        raises - 'MutexLockError' if a lock was not acquired."""

        # Don't allow double locks.
        if self.__locked:
            return

        start_time = time.time()
        while 1:
            parent_dir = os.path.dirname(self.__path)
            # Make sure the parent directory exists.
            if not os.path.isdir(parent_dir):
                raise MutexLockError, \
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
        
        

class Configuration:
    """A persistent set of program configuration variables.

    A 'Configuration' object acts as a map of configuration variables.
    The configuration is associated with a file path.  It can be made
    persistent by invoking 'Save', which writes it to that file."""

    def __init__(self, path, **initialization):
        """Create or load a configuration.

        'path' -- The path to the configuration file.

        'initialization' -- Initial configuration values."""

        self.__path = path
        self.__fields = {}
        # Initialize the fields using our '__setitem__' method.
        for key, value in initialization.items():
            self[key] = value


    def Save(self):
        """Save the configuration."""
        
        # Write the configuration to a pickle.
        pickle_file = open(self.__path, "w")
        cPickle.dump(self.__fields, pickle_file)
        pickle_file.close()


    def Load(self):
        """Load the configuration.

        raise -- 'ConfigurationError' if the configuration cannot be
        loaded."""

        # Unpickle the configuration.
        pickle_file = open(self.__path, "r")
        self.__fields = cPickle.load(pickle_file)
        pickle_file.close()


    def __getitem__(self, key):
        return self.__fields[key]


    def __setitem__(self, key, value):
        self.__fields[key] = value


    def __delitem__(self, key):
        del self.__fields[key]



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

    # FIXME: Call it "qm.ini" under Windows?
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

        assert self.__parser is not None
        
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

        # Construct the path to the user's rc file.
        # FIXME: Do something different under Windows.  
        home_directory = os.environ["HOME"]
        rc_file = os.path.join(home_directory, self.user_rc_file_name)
        # Create a parser, and read the configuration.
        parser = ConfigParser.ConfigParser()
        parser.read(rc_file)
        # Note that 'read' returns silently if the file is missing;
        # that's fine.
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


__host_name = None

def get_host_name():
    """Return the name of this computer."""

    global __host_name

    # FIXME:  Should we try the 'hostname' command here?

    # Figure out the host name the first time this function is called.
    if __host_name is None:
        # First try to look up our own address in DNS.
        try:
            name = socket.gethostbyname_ex(socket.gethostname())[0]
        except socket.error:
            name = None

        if name is None:
            # That didn't work.  Just use the local name.
            try:
                name = socket.gethostname()
            except socket.error:
                pass

        if name is None:
            # That didn't work either.  Check if the host name is stored
            # in the environment.
            try:
                name = os.environ["HOSTNAME"]
            except KeyError:
                pass

        if name is None:
            # We're stumped.  Use localhost.
            name = "localhost"

        # Store the name for next time.
        __host_name = name

    return __host_name


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

    # FIXME.  We can do better by looking into the traceback ourselves. 
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


def remove_directory_recursively(path):
    """Remove the directory at 'path' and everything under it."""

    assert os.path.isdir(path)
    # FIXME: Make this portable, or provide a Windows implementation.
    os.system('rm -rf "%s"' % path)


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


def load_module(name, path):
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
        module = imp.load_module(name, file, file_name, description)
        # Loaded successfully.  If it's contained in a package, put it
        # into that package's name space.
        if package is not None:
            setattr(package, module_name, module)
        return module
    finally:
        # Close the module file, if one was opened.
        if file is not None:
            file.close()
        
        
def load_class(name, path):
    """Load a Python class.

    'name' -- The fully-qualified (including package and module names)
    class name, for instance 'package.subpackage.module.MyClass'.  The
    class must be at the top level of the module's namespace, i.e. not
    nested in another class.

    'path' -- A sequence of directory paths in which to search for the
    containing module, analogous to 'PYTHONPATH'.

    returns -- A class object.

    raises -- 'ImportError' if the module containing the class can't be
    imported, or if there is no class with the specified name in that
    module, or if 'name' doesn't correspond to a class."""

    # Make sure the class name is fully-qualified.  It must at least be
    # in a top-level module, so there should be at least one module path
    # separator. 
    if not "." in name:
        raise ValueError, \
              "%s it not a fully-qualified class name" % name
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
            raise ImportError, "%s is not a class" % name
        return klass
    except KeyError:
        # There's no class with the requested name.
        raise ImportError, \
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

    # FIXME: Support automatic data compression here?

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


def find_program_in_path(program_name, path):
    """Attempt to locate a program in an execution path.

    'program_name' -- The name of the program to run.

    'path' -- A string encoding a list of directories (in a
    system-specifiec form) in which to look for the program.

    returns -- The path to the program, or 'None' if it was not
    found."""

    # Split the path into directories.
    # FIXME: Do the Windows thing.
    path_separator = ":"
    directories = string.split(path, path_separator)
    # Loop over directories.
    for directory in directories:
        program_path = os.path.join(directory, program_name)
        # Is there such a file, and is it executable?
        # FIXME: This won't work for Windows.
        if os.access(program_path, os.X_OK):
            # Good -- that's the result.
            return program_path
    # Couldn't find it.
    return None


def is_executable(path):
    """Return true if 'path' is an executable file."""

    # FIXME: Windows.
    return os.path.isfile(path) and os.access(path, os.X_OK)


def starts_with(text, prefix):
    """Return true if 'prefix' is a prefix of 'text'."""

    return len(text) >= len(prefix) \
           and text[:len(prefix)] == prefix


########################################################################
# variables
########################################################################

rc = RcConfiguration()
"""The configuration stored in system and user rc files."""

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

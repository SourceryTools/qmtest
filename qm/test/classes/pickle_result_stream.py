########################################################################
#
# File:   pickle_result_stream.py
# Author: Mark Mitchell
# Date:   11/25/2002
#
# Contents:
#   PickleResultStream, PickleResultReader
#
# Copyright (c) 2002, 2003 by CodeSourcery, LLC.  All rights reserved. 
#
########################################################################

########################################################################
# Imports
########################################################################

import types
import cPickle
import struct
import qm.fields
from   qm.test.file_result_stream import FileResultStream
from   qm.test.file_result_reader import FileResultReader

########################################################################
# Constants
########################################################################

# A subtlety is that because of how extension classes are loaded, we
# can't use the standard trick of using a nonce class for our sentinel,
# because the unpickler won't be able to find the class definition.  But
# 'None' has no other meaning in our format, so works fine.
_annotation_sentinel = None
"""The sentinel value that marks the beginning of an annotation."""

# Network byte order, 4 byte unsigned int
_int_format = "!I"
_int_size = struct.calcsize(_int_format)

########################################################################
# Classes
########################################################################

class PickleResultStream(FileResultStream):
    """A 'PickleResultStream' writes out results as Python pickles.

    See also 'PickleResultReader', which does the reverse."""

    _max_pinned_results = 1000
    """A limit on how many `Result's to pin in memory at once.

    Pickling an object normally pins it in memory; this is necessary
    to ensure correct behaviour when pickling multiple references to
    the same object.  We know that `Result's can't refer to each
    other, so this pinning is useless overhead; however, clearing the
    cache at every call to `WriteResult' slows down both pickling and
    unpickling by about a factor of two.  As a solution, any given
    `PickleResultStream', will clear its cache after
    `_max_pinned_results' calls to WriteResult.  This cache-clearing
    technique causes a very minor slowdown on small result streams,
    and a substantial speedup on large result streams."""

    _format_version = 1
    """The version number of the format we write.

    This is bumped every time the format is changed, to make sure that
    we can retain backwards compatibility.

    "Version 0" contains no version number, and is simply a bunch
    of 'Result's pickled one after another.

    "Version 1", and all later versions, contain a pickled version
    number as the first thing in the file.  In version 1, this is
    followed by a 4-byte unsigned integer in network byte order giving
    the address of the first annotation, followed by the file proper.
    The file proper is composed of a bunch of pickled 'Result's,
    followed by a pickled sentinel value (None), followed by a 4-byte
    unsigned integer in network-byte order, followed by the beginning of
    a new pickle whose first item is a annotation tuple, and following
    items are more 'Result's, and then another sentinel value, and so
    on.  An annotation tuple is a tuple of n items, the first of which
    is a string tagging the type of annotation, and the rest of which
    have an interpretation that depends on the tag found.  The only tag
    currently defined is "annotation", which is followed by two string
    elements giving respectively the key and the value.  The 4-byte
    integers always point to the file address of the next such integer,
    except for the last, which has a value of 0; they are used to
    quickly find all annotations."""

    arguments = [
        qm.fields.IntegerField(
            name = "protocol_version",
            description = """The pickle protocol version to use.

            There are multiple versions of the pickle protocol; in
            general, higher numbers correspond to faster operation and
            more compact files, but may produce files that cannot be
            understood by older versions of Python.

            As of 2003-06-20, the defined protocol versions are:
               0: Traditional ASCII-only format.
               1: Traditional binary format.
               2: New binary format.
              -1: Equivalent to the highest version supported by your
                  Python release.
            Pickle versions 0 and 1 can be understood by any version
            of Python; version 2 pickles can only be created or
            understood by Python 2.3 and newer.  (See PEP 307 for
            details.)

            Currently the default version is 1.

            """,
            default_value = 1,
        ),
    ]

    _is_binary_file = 1

    def __init__(self, arguments):

        # Initialize the base class.
        super(PickleResultStream, self).__init__(arguments)
        # Create initial pickler.
        self._ResetPickler()
        # We haven't processed any `Result's yet.
        self.__processed = 0

        # Write out version number.
        self.__pickler.dump(self._format_version)
        # We have no previous annotations.
        self.__last_annotation = None
        # Write out annotation header.
        self._WriteAnnotationPtr()


    def _ResetPickler(self):

        self.__pickler = cPickle.Pickler(self.file, self.protocol_version)


    def _WriteAnnotationPtr(self):

        new_annotation = self.file.tell()
        if self.__last_annotation is not None:
            self.file.seek(self.__last_annotation)
            self.file.write(struct.pack(_int_format, new_annotation))
            self.file.seek(new_annotation)
        self.file.write(struct.pack(_int_format, 0))
        self.__last_annotation = new_annotation
        self._ResetPickler()


    def WriteAnnotation(self, key, value):

        assert isinstance(key, types.StringTypes)
        assert isinstance(value, types.StringTypes)
        self.__pickler.dump(_annotation_sentinel)
        self._WriteAnnotationPtr()
        self.__pickler.dump(("annotation", key, value))


    def WriteResult(self, result):

        self.__pickler.dump(result)
        self.__processed += 1
        # If enough results have been pickeled, clear the pickling
        # cache.
        if not self.__processed % self._max_pinned_results:
            self.__pickler.clear_memo()


            
class PickleResultReader(FileResultReader):
    """A 'PickleResultReader' reads in results from pickle files.

    See also 'PickleResultStream', which does the reverse."""

    def __init__(self, arguments):

        super(PickleResultReader, self).__init__(arguments)
        self._ResetUnpickler()

        self._annotations = {}

        # Check for a version number
        try:
            version = self.__unpickler.load()
        except (EOFError, cPickle.UnpicklingError):
            raise FileResultReader.InvalidFile, \
                  "file is not a pickled result stream"
        
        if not isinstance(version, int):
            # Version 0 file, no version number; in fact, we're
            # holding a 'Result'.  So we have no metadata to load and
            # should just rewind.
            self.file.seek(0)
            self._ResetUnpickler()
        elif version == 1:
            self._ReadMetadata()
        else:
            raise QMException, "Unknown format version %i" % (version,)


    def _ResetUnpickler(self):

        self.__unpickler = cPickle.Unpickler(self.file)


    def _ReadAddress(self):

        raw = self.file.read(_int_size)
        return struct.unpack(_int_format, raw)[0]
        

    def _ReadMetadata(self):

        # We've read in the version number; next few bytes are the
        # address of the first annotation.
        addr = self._ReadAddress()
        # That advanced the read head to the first 'Result'; save this
        # spot to return to later.
        first_result_addr = self.file.tell()
        while addr:
            # Go the the address.
            self.file.seek(addr)
            # First four bytes are the next address.
            addr = self._ReadAddress()
            # Then we restart the pickle stream...
            self._ResetUnpickler()
            # ...and read in the annotation here.
            annotation_tuple = self.__unpickler.load()
            kind = annotation_tuple[0]
            if kind == "annotation":
                (key, value) = annotation_tuple[1:]
                self._annotations[key] = value
            else:
                print "Unknown annotation type '%s'; ignoring" % (kind,)
            # Now loop back and jump to the next address.

        # Finally, rewind back to the beginning for the reading of
        # 'Result's.
        self.file.seek(first_result_addr)
        self._ResetUnpickler()


    def GetAnnotations(self):

        return self._annotations


    def GetResult(self):

        while 1:
            try:
                thing = self.__unpickler.load()
            except (EOFError, cPickle.UnpicklingError):
                # When reading from a StringIO, no EOFError will be
                # raised when the unpickler tries to read from the file.
                # Instead, the unpickler raises UnpicklingError when it
                # tries to unpickle the empty string.
                return None
            else:
                if thing is _annotation_sentinel:
                    # We're looking for results, but this is an annotation,
                    # so skip over it.
                    # By skipping past the address...
                    self.file.seek(_int_size, 1)
                    self._ResetUnpickler()
                    # ...and the annotation itself.
                    self.__unpickler.noload()
                    # Now loop.
                else:
                    # We actually got a 'Result'.
                    return thing

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

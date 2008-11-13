

################################################################
# Monkey patch for LP #257276 (Hotfix-2008-08-12)
#
# This code is taken from the encodings module of Python 2.4.
# Note that this code is originally (C) CNRI and it is possibly not compatible
# with the ZPL and therefore should not live within svn.zope.org. However this
# checkin is blessed by Jim Fulton for now. The fix is no longer required with
# Python 2.5 and hopefully fixed in Python 2.4.6 release.
################################################################

# Written by Marc-Andre Lemburg (mal@lemburg.com).
# (c) Copyright CNRI, All Rights Reserved. NO WARRANTY.

def search_function(encoding):

    # Cache lookup
    entry = _cache.get(encoding, _unknown)
    if entry is not _unknown:
        return entry

    # Import the module:
    #
    # First try to find an alias for the normalized encoding
    # name and lookup the module using the aliased name, then try to
    # lookup the module using the standard import scheme, i.e. first
    # try in the encodings package, then at top-level.
    #
    norm_encoding = normalize_encoding(encoding)
    aliased_encoding = _aliases.get(norm_encoding) or \
                       _aliases.get(norm_encoding.replace('.', '_'))
    if aliased_encoding is not None:
        modnames = [aliased_encoding,
                    norm_encoding]
    else:
        modnames = [norm_encoding]
    for modname in modnames:

        if not modname or '.' in modname:
            continue

        try:
            mod = __import__(modname,
                             globals(), locals(), _import_tail)
            if not mod.__name__.startswith('encodings.'):
                continue

        except ImportError:
            pass
        else:
            break
    else:
        mod = None

    try:
        getregentry = mod.getregentry
    except AttributeError:
        # Not a codec module
        mod = None

    if mod is None:
        # Cache misses
        _cache[encoding] = None
        return None

    # Now ask the module for the registry entry
    entry = tuple(getregentry())
    if len(entry) != 4:
        raise CodecRegistryError,\
              'module "%s" (%s) failed to register' % \
              (mod.__name__, mod.__file__)
    for obj in entry:
        if not callable(obj):
            raise CodecRegistryError,\
                  'incompatible codecs in module "%s" (%s)' % \
                  (mod.__name__, mod.__file__)

    # Cache the codec registry entry
    _cache[encoding] = entry

    # Register its aliases (without overwriting previously registered
    # aliases)
    try:
        codecaliases = mod.getaliases()
    except AttributeError:
        pass
    else:
        for alias in codecaliases:
            if not _aliases.has_key(alias):
                _aliases[alias] = modname

    # Return the registry entry
    return entry


import encodings
encodings.search_function.func_code = search_function.func_code


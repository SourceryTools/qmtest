from cStringIO import StringIO


class DocFormat:
    """Base class for output formatters."""
    def __init__(self, f):
        self._mainFile = f
        b = self._bufList = []

    def close(self):
        "Copy text to main file, and close it."
        mf = self._mainFile
        for F in self._bufList:
            mf.write(F.getvalue())
        self._bufList = []

    def write(self, txt):
        "Write to latest buffer in buffer list."
        if len(self._bufList) == 0:
            self._bufList.append( StringIO() )
        self._bufList[-1].write(txt)

    def insert_buffer(self, b):
        "Insert a buffer into the current location."
        bl = self._bufList
        bl.append(b)
        bl.append( StringIO() )

#! /usr/bin/env python

import getopt, sys, urllib, urlparse

import docparse
import dochtml

def usage():
    progName = sys.argv[0]
    w = sys.stderr.write
    w('Usage:\n    '+progName+' [OPTIONS] [SRCFILE]\n\n')
    w('OPTIONS are:\n')
    w('-b BASENAME\n')
    w('--basename=BASENAME\n')
    w('\tSet basename for URLs to BASENAME\n')
    w('-o OUTPUT\n')
    w('--output=OUTPUT\n')
    w('\tSet output file to OUTPUT instead of stdout\n')

def main():
    progName = sys.argv[0]
    baseName = 'file:'
    output = 'out.htm'
    try:
        opts,args = getopt.getopt(sys.argv[1:], '?b:o:', [
            'help',
            'basename=',
            'output='
            ])
    except getopt.error, v:
        sys.stderr.write(progName + ': ' + v + '\n')
        usage()
        sys.exit(1)
    for optName,optValue in opts:
        if optName == '?' or optName == '--help':
            usage()
            sys.exit(0)
        if optName == 'b' or optName == '--basename':
            baseName = optValue
        elif optName == 'o' or optName == '--output':
            output = optValue

    if len(args) == 0:
        args = '-'
    elif len(args) > 1:
        sys.stderr.write(progName+': surplus arguments\n')
        usage()
        sys.exit(1)
    src = args[0]
    oFile = open(output, 'w')
    dh = dochtml.DocHtml(oFile)
    if src == '-':
        srcName = 'file:-'
        f = sys.stdin
    else:
        srcName = urlparse.urljoin(baseName, src)
        f = urllib.urlopen(srcName)
    print 'parse '+srcName
    data = f.read()
    if src != '-':
        f.close()

    # %%% Need to properly catch syntax errors, etc.
    xp = docparse.DocParse(dh, srcName)

    xp.feed(data)
    xp.close()
    dh.close()

main()

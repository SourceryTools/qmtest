######################################################### -*-Makefile-*-
#
# File:   standard.mk
# Author: Alex Samuel
# Date:   2000-10-20
#
# Contents:
#   GNU Makefile fragment with common rules amd configuration.
#
# Usage:
#   GNUmakefiles in subdirectories should define relevant variables,
#   and then include this fragment:
#
#     include $(TOPDIR)/standard.mk
#
#   Variables handled by these makefile rules include
#
#     SUBDIRS:      Subdirectories of the current directory.
#
#     DOCBOOK:      DocBook XML source files.
#     DOCBOOKMAIN:  The main DocBook XML source file.
#
#     DOCBITMAPS:   Bitmap files used in the HTML documentation.
# 
# Copyright (C) 2000 CodeSourcery LLC
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
# Configuration
########################################################################

# Full path to the qm project.
TOPDIR		= $(HOME)/qm

TIDY 		= tidy
TIDYFLAGS	= -wrap 72 -i --indent-spaces 1

# Jade configuration,
JADE		= jade
JADEEXTRA	= /usr/doc/jade-1.2.1/pubtext/xml.dcl

# Modular DSSSL stylesheet configuration.  The system identifiers are
# specified as relative paths, so the base of the stylesheet
# installation needs to be provided.
SGMLDIRS        += /usr/lib/sgml/stylesheets/docbook

# qm stylesheets.
HTMLSS          = $(TOPDIR)/doc/qm-html.dsl
PRINTSS         = $(TOPDIR)/doc/qm-print.dsl

# Output directory and manifest file for HTML output.  These are
# controlled by the HTML stylesheet.
HTMLDIR		= html
HTMLMANIFEST	= $(HTMLDIR)/docbook-html.manifest

# Tarball containing HTML output.
HTMLTARBALL	= $(HTMLDIR)/$(DOCBOOKMAIN:.xml=.tgz)

.PHONY:		all clean doc subdirs
.PHONY:         doc-html doc-print docbook-html docbook-print 
.PHONY:		html-dir html-output html-graphics $(HTMLTARBALL)
.PHONY:		$(SUBDIRS)

########################################################################
# Rules
########################################################################

NULLSTRING	:=
SPACE		:= $(NULLSTRING) # Leave this comment here.

all:		subdirs doc

doc:		doc-html doc-print

# Generate html and print documentation from DocBook source, if it was
# specified. 
ifneq ($(DOCBOOKMAIN),)
doc-html:	docbook-html
doc-print:	docbook-print
else
doc-html:	
doc-print:	
endif

subdirs:	$(SUBDIRS)

$(SUBDIRS):	
	cd $@ && make TOPDIR=$(TOPDIR)

docbook-html:	html-dir html-output html-graphics $(HTMLTARBALL)

html-dir:
	mkdir -p $(HTMLDIR)

# The DocBook modular stylesheets generate some sloppy HTML.  Process
# it with tidy.  Unfortunately, tidy will emit copious warnings;
# funnel them to /dev/null.  Also tidy returns non-zero indicating
# warnings; supress this by running true.
html-output:  	html-dir $(DOCBOOKMAIN) $(DOCBOOK)
	$(JADE) \
	    $(foreach dir,$(SGMLDIRS),-D$(dir)) \
	    -t sgml -d $(HTMLSS) $(JADEEXTRA) $(DOCBOOKMAIN)
	for f in html/*.html; \
	do \
	    $(TIDY) $(TIDYFLAGS) -f /dev/null -asxml -modify $${f}; \
	    true; \
	done 

# For each image file required by the HTML documentation output, copy
# it into the output directory and also add the filename to the
# manifest.
html-graphics:	html-output $(DOCBITMAPS)
	for gr in $(DOCBITMAPS); \
	do \
	    cp $${gr} $(HTMLDIR)/; \
	    echo $${gr} >> $(HTMLMANIFEST); \
	done

# Build a tarball containing the whole HTML output.
$(HTMLTARBALL):	html-output html-graphics
	tar zcf $(HTMLTARBALL) \
	    $(foreach f,$(shell cat $(HTMLMANIFEST)),$(HTMLDIR)/$(f))

docbook-print:	$(DOCBOOKMAIN) $(DOCBOOK)
	mkdir -p print
	$(JADE) \
            $(foreach dir,$(SGMLDIRS),-D$(dir)) \
	    -t tex -d $(PRINTSS) $(JADEEXTRA) $<
	if [ -n "$(DOCBITMAPS)" ]; then cp $(DOCBITMAPS) print/; fi
	texfile=$(DOCBOOKMAIN:.xml=.tex); \
	mv $${texfile} print/; \
	    cd print; \
	    pdfjadetex $${texfile} && \
	    pdfjadetex $${texfile}

########################################################################
# Pattern rules
########################################################################

# Generate .html files from .xhtml files by applying the XHTML
# processor script and then feeding the output through tidy.

%.html:		%.xhtml
	$(XHTMLPROCESS) $^ \
	  | $(TIDY) $(TIDYFLAGS) -xml \
	  > $@

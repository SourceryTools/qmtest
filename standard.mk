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

# Output directory, index HTML files, and manifest file for HTML
# output.  These are controlled by the DSSSL stylesheet for HTML.
HTMLDIR		= html
HTMLINDEX	= $(HTMLDIR)/index.html
HTMLMANIFEST	= $(HTMLDIR)/docbook-html.manifest

# Tarball containing HTML output.
HTMLTARBALL	= $(HTMLDIR)/$(DOCBOOKMAIN:.xml=.tgz)

# Output directory and output files generated with the DSSSL stylesheet
# for TeX.
PRINTDIR	= print
PRINTTEX	= $(DOCBOOKMAIN:.xml=.tex)
PRINTPDF	= $(DOCBOOKMAIN:.xml=.pdf)

.PHONY:		all clean doc subdirs
.PHONY:         doc-html doc-print docbook-html docbook-print 
.PHONY:		$(SUBDIRS)

########################################################################
# Rules
########################################################################

NULLSTRING	:=
SPACE		:= $(NULLSTRING) # Leave this comment here.

all:		subdirs doc

subdirs:	$(SUBDIRS)

$(SUBDIRS):	
	cd $@ && make TOPDIR=$(TOPDIR)

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

docbook-html:	$(HTMLINDEX) $(HTMLTARBALL)

docbook-print:	$(PRINTDIR)/$(PRINTPDF)


# The DocBook modular stylesheets generate some sloppy HTML.  Process
# it with tidy.  Unfortunately, tidy will emit copious warnings;
# funnel them to /dev/null.  Also tidy returns non-zero indicating
# warnings; supress this by running true.
#
# For each image file required by the HTML documentation output, copy
# it into the output directory and also add the filename to the
# manifest.
$(HTMLMANIFEST) $(HTMLINDEX): \
	 	$(DOCBOOKMAIN) $(DOCBOOK) $(DOCBITMAP)
	mkdir -p $(HTMLDIR)
	$(JADE) \
	    $(foreach dir,$(SGMLDIRS),-D$(dir)) \
	    -t sgml -d $(HTMLSS) \
	    $(JADEEXTRA) \
	    $(DOCBOOKMAIN)
	for f in html/*.html; \
	do \
	    $(TIDY) $(TIDYFLAGS) -f /dev/null -asxml -modify $${f}; \
	    true; \
	done 
	for gr in $(DOCBITMAPS); \
	do \
	    cp $${gr} $(HTMLDIR)/; \
	    echo $${gr} >> $(HTMLMANIFEST); \
	done

# Build a tarball containing the whole HTML output.
$(HTMLTARBALL):	$(HTMLMANIFEST)
	tar zcf $(HTMLTARBALL) \
	    $(foreach f,$(shell cat $(HTMLMANIFEST)),$(HTMLDIR)/$(f))

# Jade places the output TeX source file in the current directory, so
# move it where we want it afterwards.
$(PRINTDIR)/$(PRINTTEX): \
		$(DOCBOOKMAIN) $(DOCBOOK)
	mkdir -p $(PRINTDIR)
	$(JADE) \
            $(foreach dir,$(SGMLDIRS),-D$(dir)) \
	    -t tex -d $(PRINTSS) \
	    $(JADEEXTRA) \
	    $<
	mv $(PRINTTEX) $(PRINTDIR)/

# Process the TeX file to PDF, in the print directory.  TEXPSHEADERS
# must be set to the DocBook source directory so that TeX can find the
# image files referenced in the document.  
$(PRINTDIR)/$(PRINTPDF): \
		$(PRINTDIR)/$(PRINTTEX)
	cd $(PRINTDIR) \
	    && TEXPSHEADERS=..: pdfjadetex $(PRINTTEX) 


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
#     HTML:         HTML files to be generated from XHTML.
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
TIDYFLAGS	= -wrap 72 -i

XHTMLPROCESS	= $(TOPDIR)/doc/process-xhtml.py

.PHONY:		all clean doc subdirs
.PHONY:		$(SUBDIRS)

########################################################################
# Rules
########################################################################

all:		subdirs doc

doc:		$(HTML)

subdirs:	$(SUBDIRS)

$(SUBDIRS):	
	cd $@ && make TOPDIR=$(TOPDIR)

########################################################################
# Pattern rules
########################################################################

# Generate .html files from .xhtml files by applying the XHTML
# processor script and then feeding the output through tidy.

%.html:		%.xhtml
	$(XHTMLPROCESS) $^ \
	  | $(TIDY) $(TIDYFLAGS) -xml \
	  > $@

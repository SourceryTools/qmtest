<!--

  File:   qm-html.dsl
  Author: Alex Samuel
  Date:   2000-11-09

  Contents:
    DSSSL style sheet for generating HTML from DocBook documents.

  Copyright (C) 2000, 2001 CodeSourcery LLC

  Permission is hereby granted, free of charge, to any person
  obtaining a copy of this software and associated documentation files
  (the "Software"), to deal in the Software without restriction,
  including without limitation the rights to use, copy, modify, merge,
  publish, distribute, sublicense, and/or sell copies of the Software,
  and to permit persons to whom the Software is furnished to do so,
  subject to the following conditions:

  The above copyright notice and this permission notice shall be
  included in all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
  LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
  ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
  CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.

-->
<!DOCTYPE style-sheet PUBLIC "-//James Clark//DTD DSSSL Style Sheet//EN" 
[
 <!-- This style sheet extends Norman Walsh's Modular DSSSL Docbook
      Stylesheet for HTML.  -->

 <!ENTITY dbstyle 
  PUBLIC "-//Norman Walsh//DOCUMENT DocBook HTML Stylesheet//EN" 
  CDATA DSSSL>
]> 

<style-sheet>
<style-specification use="docbook">
<style-specification-body> 

;; Place output in the html/ subdirectory.
(define use-output-dir #t)
(define %output-dir% "html")

;; Use the extension .html for output files.
(define %html-ext% ".html")

;; The main file is named index.
(define %root-filename% "index")

;; Turn on Cascading Style Sheets markup in the resulting HTML.
(define %css-decoration% #t)

;; Assign numbers to sections and subsections.
(define %section-autolabel% #t)

;; Don't place the first section of each chapter in the same chunk as
;; the chapter head.
(define (chunk-skip-first-element-list) (list))

;; Write a manifest of created files to docbook-html.manifest.
(define html-manifest #t)
(define html-manifest-filename "docbook-html.manifest")

;; Use element ids to generate chunk filenames
(define %use-id-as-filename% #t)

;; Emit legal notices in a separate chunk.
(define %generate-legalnotice-link% #t)

</style-specification-body>
</style-specification>
<external-specification id="docbook" document="dbstyle">
</style-sheet>

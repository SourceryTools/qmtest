<!--

  File:   qm-sgml.dsl
  Author: Alex Samuel
  Date:   2000-11-09

  Contents:
    DSSSL style sheet for generating HTML from DocBook documents.

  Copyright (C) 2000, 2001, 2002 CodeSourcery LLC

  For license terms see the file COPYING.

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

;; Use element ids to generate chunk filenames
(define %use-id-as-filename% #t)

;; Emit legal notices in a separate chunk.
(define %generate-legalnotice-link% #t)

</style-specification-body>
</style-specification>
<external-specification id="docbook" document="dbstyle">
</style-sheet>

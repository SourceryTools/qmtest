<!--

  File:   qm-print.dsl
  Author: Alex Samuel
  Date:   2000-11-10

  Contents:
    DSSSL style sheet for generating hardcopy from DocBook documents.

  Copyright (C) 2000 CodeSourcery LLC

  For license terms see the file COPYING.

-->
<!DOCTYPE style-sheet PUBLIC "-//James Clark//DTD DSSSL Style Sheet//EN" 
[
 <!-- This style sheet extends Norman Walsh's Modular DSSSL Docbook
      Print Stylesheet.  -->

 <!ENTITY dbstyle 
  PUBLIC "-//Norman Walsh//DOCUMENT DocBook Print Stylesheet//EN" 
  CDATA DSSSL>
]> 

<style-sheet>
<style-specification use="docbook">
<style-specification-body> 

;; Customizations here.

;; Number chapters and sections.
(define %chapter-autolabel% #t)
(define %section-autolabel% #t)

</style-specification-body>
</style-specification>
<external-specification id="docbook" document="dbstyle">
</style-sheet>

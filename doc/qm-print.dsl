<!--

  File:   qm-print.dsl
  Author: Alex Samuel
  Date:   2000-11-10

  Contents:
    DSSSL style sheet for generating hardcopy from DocBook documents.

  Copyright (C) 2000 CodeSourcery LLC

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

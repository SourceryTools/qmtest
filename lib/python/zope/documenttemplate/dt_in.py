##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Sequence insertion

       A sequence may be inserted using an 'in' command.  The 'in'
       command specifies the name of a sequence object and text to
       be inserted for each element in the sequence.

       The EPFS syntax for the in command is::

          %(in name)[
               text
          %(in name)]

       The HTML syntax for the in command is::

          <dtml-in name>
               text
          </dtml-in name>

      See the example below that shows how 'if', 'else', and 'in' commands
      may be combined to display a possibly empty list of objects.

      The text included within an 'in' command will be refered to
      as an 'in' block.

    Synopsis

      If the variable 'sequence' exists as a sequence, a simple case
      of the 'in' tag is used as follows::

         <dtml-in sequence>some markup</dtml-in>

      A more complete case is used as follows::

        <dtml-in sequence sort=age>
          <dtml-var sequence-number>) <dtml-var age>
        </dtml-in>

    Attributes

      sort -- Define the sort order for sequence items.  If an item in
      the sequence does not define

      sort_expr -- This allows an expression to control sort order.

      reverse -- Reverse the sequence (may be combined with sort).  Note
      that this can cause a huge memory use in lazy activation instances.

      reverse_expr -- This allows reversing to be controlled by an expression.

      Within an 'in' block, variables are substituted from the
      elements of the iteration.  The elements may be either
      instance or mapping objects.  In addition, the variables:

         'sequence-item' -- The element.

         'sequence-var-nnn' -- The value of a specific named attribute
           of the item, where 'nnn' is the name.  For example, to get
           an items 'title' attribute, use 'sequence-var-title'.  This
           construct is most useful in an 'if' tag to test whether an
           attribute is present, because the attribute lookup will be
           extended to the full document template namespace.

         'sequence-key' -- The key associated with the element in an
           items list. See below.

         'sequence-index' -- The index, starting from 0, of the
           element within the sequence.

         'sequence-number' -- The index, starting from 1, of the
           element within the sequence.

         'sequence-letter' -- The index, starting from 'a', of the
           element within the sequence.

         'sequence-Letter' -- The index, starting from 'A', of the
           element within the sequence.

         'sequence-roman' -- The index, starting from 'i', of the
           element within the sequence.

         'sequence-Roman' -- The index, starting from 'I', of the
           element within the sequence.

         'sequence-start' -- A variable that is true if the element
           being displayed is the first of the displayed elements,
           and false otherwise.

         'sequence-end' -- A variable that is true if the element
           being displayed is the last of the displayed elements,
           and false otherwise.

      are defined for each element.

      Normally, 'in' blocks are used to iterate over sequences of
      instances.  If the optional parameter 'mapping' is specified
      after the sequence name, then the elements of the sequence
      will be treated as mapping objects.

      An 'in' command may be used to iterate over a sequence of
      dictionary items.  If the elements of the iteration are
      two-element tuples, then then the template code given in the
      'in' block will be applied to the second element of each
      tuple and may use a variable, 'sequence-key' to access the
      first element in each tuple.

    Batch sequence insertion

      When displaying a large number of objects, it is sometimes
      desirable to display just a sub-sequence of the data.
      An 'in' command may have optional parameters,
      as in::

          <dtml-in values start=start_var size=7>

      The parameter values may be either integer literals or
      variable names.

      Up to five parameters may be set:

          'start'   -- The number of the first element to be shown,
                       where elements are numbered from 1.

          'end'     -- The number of the last element to be shown,
                       where elements are numbered from 1.

          'size'    -- The desired number of elements to be shown at
                       once.

          'orphan'  -- The desired minimum number of objects to be
                       displayed.  The default value for this
                       parameter is 3.

          'overlap' -- The desired overlap between batches. The
                       default is no overlap.

      Typically, only 'start' and 'size' will be specified.

      When batch insertion is used, several additional variables are
      defined for use within the sequence insertion text:

          'sequence-query' -- The original query string given in a get
             request with the form variable named in the 'start'
             attribute removed.  This is extremely useful when
             building URLs to fetch another batch.

             To see how this is used, consider the following example::

                 <dtml-in search_results size=20 start=batch_start>

                    ... display rows

                    <dtml-if sequence-end> <dtml-if next-sequence>
                      <a href="<dtml-var URL>/<dtml-var sequence-query
                          >&batch_start=<dtml-var
                          next-sequence-start-number>">
                      (Next <dtml-var next-sequence-size> results)
                      </a>
                    </dtml-if> </dtml-if>

                 </dtml-in>

             If the original URL is: 'foo/bar?x=1&y=2', then the
             rendered text (after row data are displayed) will be::

                      <a href="foo/bar?x=1&y=2&batch_start=20">
                      (Next 20 results)
                      </a>

             If the original URL is: 'foo/bar?batch_start=10&x=1&y=2',
             then the rendered text (after row data are displayed)
             will be::

                      <a href="foo/bar?x=1&y=2&batch_start=30">
                      (Next 20 results)
                      </a>

          'sequence-step-start-index' -- The index, starting from 0,
             of the start of the current batch.

          'sequence-step-end-index' -- The index, starting from 0, of
             the end of the current batch.

          'sequence-step-size' -- The batch size used.

          'previous-sequence' -- This variable will be true when the
             first element is displayed and when the first element
             displayed is not the first element in the sequence.

          'previous-sequence-start-index' -- The index, starting from
             0, of the start of the batch previous to the current
             batch.

          'previous-sequence-end-index' -- The index, starting from
             0, of the end of the batch previous to the current
             batch.

          'previous-sequence-size' -- The size of the batch previous to
             the current batch.

          'previous-batches' -- A sequence of mapping objects
             containing information about all of the batches prior
             to the batch being displayed.

             Each of these mapping objects include the following
             variables:

                batch-start-index -- The index, starting from
                   0, of the beginning of the batch.

                batch-end-index -- The index, starting from
                   0, of the end of the batch.

                batch-size -- The size of the batch.

          'next-sequence' -- This variable will be true when the last
             element is displayed and when the last element
             displayed is not the last element in the sequence.

          'next-sequence-start-index' -- The index, starting from
             0, of the start of the batch after the current
             batch.

          'next-sequence-end-index' -- The index, starting from
             0, of the end of the batch after the current
             batch.

          'next-sequence-size' -- The size of the batch after
             the current batch.

          'next-batches' -- A sequence of mapping objects
             containing information about all of the batches after
             the batch being displayed.

             Each of these mapping objects include the following
             variables:

                batch-start-index -- The index, starting from
                   0, of the beginning of the batch.

                batch-end-index -- The index, starting from
                   0, of the end of the batch.

                batch-size -- The size of the batch.

      For each of the variables listed above with names ending in
      "-index", there are variables with names ending in "-number",
      "-roman", "-Roman", "-letter", and "-Letter" that are indexed
      from 1, "i", "I", "a", and "A", respectively.  In addition,
      for every one of these variables there are variables with
      names ending in "-var-xxx", where "xxx" is an element
      attribute name or key.

    Summary statistics

      When performing sequence insertion, special variables may be
      used to obtain summary statistics.  To obtain a summary
      statistic for a variable, use the variable name:
      'statistic-name', where 'statistic' is a statistic name and
      'name' is the name of a data variable.

      Currently supported statistic names are:

        total -- The total of numeric values.

        count -- The total number of non-missing values.

        min -- The minimum of non-missing values.

        max -- The maximum of non-missing values.

        median -- The median of non-missing values.

        mean -- The mean of numeric values values.

        variance -- The variance of numeric values computed with a
          degrees of freedom equal to the count - 1.

        variance-n -- The variance of numeric values computed with a
          degrees of freedom equal to the count.

        standard-deviation -- The standard deviation of numeric values
          computed with a degrees of freedom equal to the count - 1.

        standard-deviation-n -- The standard deviation of numeric
          values computed with a degrees of freedom equal to the count.

      Missing values are 'None'.

    'else' continuation tag within in

      An 'else' tag may be used as a continuation tag in the 'in' tag.
      The source after the 'else' tag is inserted if:

        - The sequence given to the 'in' tag is of zero length, or

        - The 'previous' attribute was used and their are no
          previous batches, or

        - The 'next' attribute was used and their are no
          next batches, or

$Id: dt_in.py 38178 2005-08-30 21:50:19Z mj $
"""

from zope.documenttemplate.dt_util import ParseError, parse_params, name_param
from zope.documenttemplate.dt_util import render_blocks, ValidationError, Eval

import re
from zope.documenttemplate.dt_insv import sequence_variables, opt
from types import StringType, ListType, TupleType, IntType, FloatType, NoneType


class InFactory:
    blockContinuations = ('else',)
    name = 'in'

    def __call__(self, context, blocks):
        i = InClass(context, blocks)
        if i.batch:
            return i.renderwb
        else:
            return i.renderwob

In = InFactory()

class InError(Exception):
    """Strings are not allowed as input to the in tag"""

class InClass:
    elses = None
    expr = sort = batch = mapping = None
    start_name_re = None
    reverse = None
    sort_expr = reverse_expr = None

    def __init__(self, context, blocks):
        tname, args, section = blocks[0]
        args=parse_params(args, name='', start='1',end='-1',size='10',
                          orphan='3',overlap='1',mapping=1,
                          skip_unauthorized=1,
                          previous=1, next=1, expr='', sort='',
                          reverse=1, sort_expr='', reverse_expr='')
        self.args=args
        has_key=args.has_key

        if has_key('sort'):
            self.sort=sort=args['sort']
            if sort=='sequence-item': self.sort=''

        if has_key('sort_expr'):
            self.sort_expr = Eval(context, args['sort_expr'])

        if has_key('reverse_expr'):
            self.reverse_expr = Eval(context, args['reverse_expr'])

        if has_key('reverse'):
            self.reverse = args['reverse']

        if has_key('mapping'):
            self.mapping = args['mapping']
        for n in 'start', 'size', 'end':
            if has_key(n):
                self.batch=1

        for n in 'orphan','overlap','previous','next':
            if has_key(n) and not self.batch:
                raise ParseError(
                    """
                    The %s attribute was used but neither of the
                    <code>start</code>, <code>end</code>, or <code>size</code>
                    attributes were used.
                    """ % n, 'in')

        if has_key('start'):
            v = args['start']
            if isinstance(v, StringType):
                try: v.atoi()
                except:
                    self.start_name_re = re.compile(
                        '&+'+
                        ''.join(map(lambda c: "[%s]" % c, v))+
                        '=[0-9]+&+')

        name, expr = name_param(context, args, 'in', 1)
        if expr is not None:
            expr = expr.eval
        self.__name__, self.expr = name, expr
        self.section = section.blocks
        if len(blocks) > 1:
            if len(blocks) != 2: raise ParseError(
                'too many else blocks', 'in')
            tname, args, section = blocks[1]
            args=parse_params(args, name='')
            if args:
                ename = name_param(context, args)
                if ename != name:
                    raise ParseError(
                        'name in else does not match in', 'in')
            self.elses = section.blocks


    def renderwb(self, md):
        expr = self.expr
        name = self.__name__
        if expr is None:
            sequence = md[name]
            cache = {name: sequence }
        else:
            sequence = expr(md)
            cache = None

        if not sequence:
            if self.elses:
                return render_blocks(self.elses, md)
            return ''

        if isinstance(sequence, StringType):
            raise InError('Strings are not allowed as input to the in tag.')


        section = self.section
        params = self.args

        mapping = self.mapping

        if self.sort_expr is not None:
            self.sort = self.sort_expr.eval(md)
            sequence = self.sort_sequence(sequence)
        elif self.sort is not None:
            sequence = self.sort_sequence(sequence)

        if self.reverse_expr is not None and self.reverse_expr.eval(md):
            sequence = self.reverse_sequence(sequence)
        elif self.reverse is not None:
            sequence = self.reverse_sequence(sequence)

        next = previous = 0
        try:
            start = int_param(params, md, 'start', 0)
        except:
            start=1
        end = int_param(params, md, 'end', 0)
        size = int_param(params, md, 'size', 0)
        overlap = int_param(params, md, 'overlap', 0)
        orphan = int_param(params, md, 'orphan', '3')
        start, end, sz = opt(start, end, size, orphan, sequence)
        if params.has_key('next'):
            next = 1
        if params.has_key('previous'):
            previous = 1

        last = end - 1
        first = start - 1

        try:
            query_string = md['QUERY_STRING']
        except:
            query_string = ''

        vars = sequence_variables(sequence,'?' + query_string,
                                  self.start_name_re)
        kw = vars.data
        kw['mapping'] = mapping
        kw['sequence-step-size'] = sz
        kw['sequence-step-overlap'] = overlap
        kw['sequence-step-start'] = start
        kw['sequence-step-end'] = end
        kw['sequence-step-start-index'] = start - 1
        kw['sequence-step-end-index'] = end - 1
        kw['sequence-step-orphan'] = orphan

        push = md._push
        pop = md._pop
        render = render_blocks

        if cache:
            push(cache)
        push(vars)
        try:
            if previous:
                if first > 0:
                    pstart, pend, psize = opt(0, first+overlap,
                                              sz, orphan, sequence)
                    kw['previous-sequence'] = 1
                    kw['previous-sequence-start-index'] = pstart - 1
                    kw['previous-sequence-end-index'] = pend - 1
                    kw['previous-sequence-size'] = pend + 1 - pstart
                    result=render(section,md)

                elif self.elses:
                    result = render(self.elses, md)
                else:
                    result = ''
            elif next:
                try:
                    # The following line is a sneaky way to test whether
                    # there are more items, without actually
                    # computing a length:
                    sequence[end]
                except IndexError:
                    if self.elses:
                        result = render(self.elses, md)
                    else:
                        result = ''
                else:
                    pstart, pend, psize = opt(end+1-overlap, 0,
                                              sz, orphan, sequence)
                    kw['next-sequence'] = 1
                    kw['next-sequence-start-index'] = pstart - 1
                    kw['next-sequence-end-index'] = pend - 1
                    kw['next-sequence-size'] = pend + 1 - pstart
                    result = render(section, md)
            else:
                result = []
                append = result.append
                validate = md.validate
                for index in range(first,end):
                    # preset
                    kw['previous-sequence'] = 0
                    # now more often defined then previously
                    kw['next-sequence'] = 0

                    if index==first or index==last:
                        # provide batching information
                        if first > 0:
                            pstart, pend, psize = opt(0, first + overlap,
                                                      sz, orphan, sequence)
                            if index == first:
                                kw['previous-sequence'] = 1
                            kw['previous-sequence-start-index'] = pstart - 1
                            kw['previous-sequence-end-index'] = pend - 1
                            kw['previous-sequence-size'] = pend + 1 - pstart
                        try:
                            # The following line is a sneaky way to
                            # test whether there are more items,
                            # without actually computing a length:
                            sequence[end]
                            pstart, pend, psize = opt(end + 1 - overlap, 0,
                                                      sz, orphan, sequence)
                            if index == last:
                                kw['next-sequence'] = 1
                            kw['next-sequence-start-index'] = pstart - 1
                            kw['next-sequence-end-index'] = pend - 1
                            kw['next-sequence-size'] = pend + 1 - pstart
                        except:
                            pass

                    if index == last:
                        kw['sequence-end'] = 1

                    client = sequence[index]

                    if validate is not None:
                        try:
                            vv = validate(sequence, sequence, None, client,md)
                        except:
                            vv = 0
                        if not vv:
                            if (params.has_key('skip_unauthorized') and
                                params['skip_unauthorized']):
                                if index == first:
                                    kw['sequence-start'] = 0
                                continue
                            raise ValidationError(index)

                    kw['sequence-index'] = index
                    if isinstance(client, TupleType) and len(client) == 2:
                        client = client[1]

                    if mapping:
                        push(client)
                    else:
                        md._push_instance(client)

                    try:
                        append(render(section, md))
                    finally:
                        pop(1)

                    if index == first:
                        kw['sequence-start'] = 0

                result = ''.join(result)

        finally:
            if cache:
                pop()
            pop()

        return result

    def renderwob(self, md):
        """RENDER WithOutBatch"""
        expr = self.expr
        name = self.__name__
        if expr is None:
            sequence = md[name]
            cache = {name: sequence }
        else:
            sequence = expr(md)
            cache = None

        if not sequence:
            if self.elses:
                return render_blocks(self.elses, md)
            return ''

        if isinstance(sequence, StringType):
            raise InError('Strings are not allowed as input to the in tag.')

        section = self.section
        mapping = self.mapping


        if self.sort_expr is not None:
            self.sort = self.sort_expr.eval(md)
            sequence = self.sort_sequence(sequence)
        elif self.sort is not None:
            sequence = self.sort_sequence(sequence)

        if self.reverse_expr is not None and self.reverse_expr.eval(md):
            sequence = self.reverse_sequence(sequence)
        elif self.reverse is not None:
            sequence = self.reverse_sequence(sequence)

        vars = sequence_variables(sequence)
        kw = vars.data
        kw['mapping'] = mapping

        l = len(sequence)
        last = l - 1

        push = md._push
        pop = md._pop
        render = render_blocks
        get = self.args.get

        if cache:
            push(cache)
        push(vars)
        try:
            result = []
            append = result.append
            validate = md.validate
            for index in range(l):
                if index == last:
                    kw['sequence-end'] = 1
                client = sequence[index]

                if validate is not None:
                    try:
                        vv = validate(sequence, sequence, None, client, md)
                    except:
                        vv = 0
                    if not vv:
                        if get('skip_unauthorized'):
                            if index == 1:
                                kw['sequence-start'] = 0
                            continue
                        raise ValidationError(index)

                kw['sequence-index'] = index
                if isinstance(client, TupleType) and len(client) == 2:
                    client = client[1]

                if mapping:
                    push(client)
                else:
                    md._push_instance(client)

                try:
                    append(render(section, md))
                finally:
                    pop()
                if index == 0:
                    kw['sequence-start'] = 0

            result = ''.join(result)

        finally:
            if cache:
                pop()
            pop()

        return result

    def sort_sequence(self, sequence):

        # Modified with multiple sort fields by Ross Lazarus
        # April 7 2000 rossl@med.usyd.edu.au
        # eg <dtml in "foo" sort=akey,anotherkey>

        sort = self.sort
        sortfields = sort.split(',')   # multi sort = key1,key2
        multsort = len(sortfields) > 1 # flag: is multiple sort
        mapping = self.mapping
        isort = not sort
        s = []
        for client in sequence:
            k = None
            if isinstance(client, TupleType) and len(client)==2:
                if isort:
                    k = client[0]
                v = client[1]
            else:
                if isort:
                    k = client
                v = client

            if sort:
                if multsort: # More than one sort key.
                    k = []
                    for sk in sortfields:
                        try:
                            if mapping:
                                akey = v[sk]
                            else:
                                akey = getattr(v, sk)
                        except AttributeError, KeyError:
                            akey = None
                        if not basic_type(akey):
                            try:
                                akey = akey()
                            except:
                                pass
                        k.append(akey)
                else: # One sort key.
                    try:
                        if mapping:
                            k = v[sort]
                        else:
                            k = getattr(v, sort)
                    except AttributeError, KeyError:
                        k = None
                    if not basic_type(type(k)):
                        try:
                            k = k()
                        except:
                            pass

            s.append((k,client))

        s.sort()

        sequence = []
        for k, client in s:
            sequence.append(client)
        return sequence


    def reverse_sequence(self, sequence):
        s = list(sequence)
        s.reverse()
        return s


basic_type = {StringType: 1, IntType: 1, FloatType: 1, TupleType: 1,
              ListType: 1, NoneType: 1}.has_key

def int_param(params, md, name, default=0, st=StringType):
    try:
        v = params[name]
    except:
        v = default
    if v:
        try:
            v = v.atoi()
        except:
            v = md[v]
            if isinstance(v, st):
                v = v.atoi()
    return v

########################################################################
#
# File:   graph.py
# Author: Benjamin Chelf
# Date:   2001-03-13
#
# Contents:
#   Functions for use with graphs.
#
# Copyright (c) 2001 by CodeSourcery, LLC.  All rights reserved. 
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
# functions
########################################################################

def __sort_helper(nodes, edges, visited, queue, check_list):
    """Performs a dfs on the graph to check for cycles and compute order.

    'nodes' -- A sequence of vertices to be traversed in this part of the
    walk.

    'edges' -- A mapping representing directed edges in a graph. Each
    element in the 'nodes' list is a valid key in the map. The
    corresponding value is a list of predecessors for that node. This
    list may be empty if the node has no predecessors.

    'visited' -- A list of nodes that hvae already been visited.

    'queue' -- The queue of tasks to be performed.
    
    'check_list' -- If the user wants to verify that the nodes in the
    predecessor lists are all in the nodes given, use this array to hold
    the list of nodes. Otherwise, this should be None.
    
    returns -- 1 if there is a cycle, 0 otherwise."""

    new_visited = visited + [ None ]
    new_queue = queue

    for node in nodes:
        if check_list != None and node not in check_list:
            raise ValueError, "predecessor not in nodes"

        # If we've already visited a node, we have a cycle.
        if node in visited:
            return 0

        # If we have not already added this node to the queue, walk up the
        # predecessors and add it to the queue.
        if node not in new_queue:
            # For each node in the list, take that node (by putting it in the
            # visited list) and recurse up its predecessors.
            new_visited[len(new_visited) - 1] = node
            ret_val = __sort_helper(edges[node], edges, new_visited,
                                    new_queue, check_list)
            if ret_val == 0:
                return 0
            else:
                new_queue = ret_val
            # Add the node to the end of the queue once we've processed
            # all of its predecessors.
            new_queue = new_queue + [ node ]

    return new_queue

    
def topological_sort(nodes, edges, complete_graph=0):
    """Topologically sort a sequence 'nodes'.
    
    'nodes' -- A sequence of arbitrary objects.
    
    'edges' -- A mapping representing dependencies.  Each element
    of 'nodes' is a valid key in the map.  The corresponding value
    is a sequence of predecessors in the graph, which may be empty.
    
    'complete_graph' -- If true, 'nodes' contains all the nodes in
    the graph; this function will raise a 'ValueError' if it
    encounters a predecessor that is not in 'nodes.  If false,
    'nodes' may not initially contain all the nodes in the graph;
    this function will add additional nodes to the sort result to
    satisfy predecessor relationships.
    
    returns -- A sequence containing the elements of 'nodes'
    arranged in a topological sort.  If 'complete_graph' is false,
    the result may contain other nodes as well."""
    
    if complete_graph:
        ret_val = __sort_helper(nodes, edges, [], [], nodes)
    else:
        ret_val = __sort_helper(nodes, edges, [], [], None)

    if ret_val == 0:
        raise ValueError, "Given graph has a cycle"

    return ret_val


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

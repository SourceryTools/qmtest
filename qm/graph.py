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

"""Functions for performing computations on directed graphs.

In this module, the set of nodes in a graph is represented by a sequence
of objects, each corresponding to one node.  The order in which the
nodes are specified is not significant, but each node should only be
specified once.  Nodes can be any hashable type, and node identity is
established using ordinary comarisons.

The set of directed edges in a graph is represented by a map.  A key in
this map is a node, and the corresponding value is the sequence of
predecessors of this node.  If a node doesn't appear as a key in this
map, it is assumed to have no predecessors."""

########################################################################
# exceptions
########################################################################

class CycleError(Exception):
    """A cycle found in a graph during a computation that forbids it.

    The exception argument is one node involved in the cycle."""

    pass



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

    'visited' -- A list of nodes that have already been visited.

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
            predecessors = edges.get(node, [])
            ret_val = __sort_helper(predecessors, edges, new_visited,
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


def _partition(node, edges, partition_map, in_progress=()):
    """Add 'node' and its predecessors to the 'partition_map'.

    'node' -- A node to add to the partition map.

    'edges' -- The map of the edges of the entire graph.

    'partition_map' -- A map from a node to the partition containing it.
    The partition is represented as a list of nodes.

    'in_progress' -- A tuple of nodes being processed in the recursive
    call chain of this function; used for detecting loops.

    postcondition -- 'partition_map' contains entries for 'node' and all
    of its predecessors.

    raises -- 'CycleError' if a directed cycle is detected in the
    graph."""

    # Are we currently processing this node?
    if node in in_progress:
        # Yes.  We've found a cycle.
        raise CycleError, node

    # Skip this node if we've already processed it.
    if partition_map.has_key(node):
        return

    # Start processing this node.
    in_progress = (node, ) + in_progress

    # Extract the node's predecessors from the graph.
    predecessors = edges.get(node, [])

    # Fully process each predecessor.
    for predecessor in predecessors:
        _partition(predecessor, edges, partition_map, in_progress)

    if len(predecessors) > 0:
        # Join all predecessor's partitions into a single one.  Start
        # with the first predecessor's partition.
        partition = partition_map[predecessors[0]]
        # Successively join with each other predecessor's partition.
        for predecessor in predecessors[1:]:
            # Get 'predecessor's partition.
            predecessor_partition = partition_map[predecessor]
            # Is it already in 'partition'?
            if predecessor_partition is not partition:
                # No.  Add the nodes in 'predecessor's partition to
                # 'partition'.
                partition.extend(predecessor_partition)
                # Point the nodes in 'predecessor's partition (including
                # 'predecessor' itself) at 'partition'.
                for pn in predecessor_partition:
                    partition_map[pn] = node_partition
        # Put 'node' into 'partition'.
        partition.append(node)
    else:
        # 'node' has no predecessors, so start a new partition.
        partition = [node]
        
    partition_map[node] = partition


def partition_as_map(nodes, edges):
    """Partition a graph into disconnected subgraphs.

    'nodes' -- A sequence of graph nodes.

    'edges' -- A map of graph edges.

    returns -- A map from a node to the partition containing it.  The
    partition is represented as a list of nodes contained in it.  The
    partition list objects in the map are shared.  Each partition is
    topologically sorted.

    raises -- 'CycleError' if a directed cycle is detected in the
    graph."""
    
    partition_map = {}
    for node in nodes:
        _partition(node, edges, partition_map)
    return partition_map


def partition(nodes, edges):
    """Partition a graph into disconnected subgraphs.

    'nodes' -- A sequence of graph nodes.

    'edges' -- A map of graph edges.

    returns -- A sequence of partitions.  Each partition is represented
    by a sequence of nodes it contains, topologically sorted.

    raises -- 'CycleError' if a directed cycle is detected in the
    graph."""

    # Construct the partitions as a map.
    partition_map = partition_as_map(nodes, edges)
    # Now extract a single occurrence of each partition.
    partitions = []
    for node, partition in partition_map.items():
        # Select this occurrence if 'node' is the first element of
        # 'partition'.  This way we get exactly one of each partition.
        if node == partition[0]:
            partitions.append(partition)
    return partitions


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:

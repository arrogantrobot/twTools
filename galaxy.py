#!/usr/bin/env python

from graph import Graph

class Galaxy(Graph):
  def __init__(self, graph_dict={}):
    super(Galaxy, self).__init__(graph_dict)

  def get_neighbors(self, vertex):
    """ get the neighboring vertices """
    if type(vertex) == "str":
      return self.graph_dict[vertex]
    else:
      return self.graph_dict[str(vertex)]

  def depth_limited_explore(self, sector, depth):
    if depth == 0:
      return
    neighborhood = self.get_neighbors(sector)
    self.__output[sector] = neighborhood
    self.__explored.add(sector)
    for neighbor in neighborhood:
      if neighbor not in self.__explored:
        self.depth_limited_explore(neighbor, depth - 1)

  def get_map(self, start, depth):
    self.__explored = set([])
    self.__output = {}
    self.depth_limited_explore(start, depth)
    return self.__output

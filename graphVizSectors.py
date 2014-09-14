#!/usr/bin/env python

import sys
from galaxy import Galaxy
from dictgraphviz import dict_to_digraph

def load_warps(path):
  sectors = {}
  with open(sys.argv[1]) as fh:
    fh.readline()
    for l in fh:
      line = l.strip().split()
      if len(line) < 2:
        break
      sectors[line[0]] = line[1:]
  return sectors


if __name__ == "__main__":
  galaxy = Galaxy(load_warps(sys.argv[1]))
  start = int(sys.argv[2])
  depth = int(sys.argv[3])
  output = galaxy.get_map(start, depth)
  print dict_to_digraph(output, "sector{0}depth{1}".format(start, depth))


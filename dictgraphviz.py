#!/usr/bin/env python

def dict_to_digraph(graph, name):
  answer = "strict digraph {0} {{\n".format(name)
  answer += "    concentrate=true\n"
  for v in graph:
    if len(graph[v]) > 1:
      answer += "    {0} -> {{ {1} }};\n".format(v, ", ".join(graph[v]))
    elif len(graph[v]) > 0:
      answer += "    {0} -> { {1} };\n".format(v, graph[v])

  answer += "}\n"
  return answer

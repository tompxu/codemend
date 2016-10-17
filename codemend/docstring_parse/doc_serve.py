"""
Serves ElemDoc items.

"""

import csv
from itertools import imap
from collections import defaultdict
import string

from codemend.docstring_parse.elemdoc import ElemDoc
from codemend.docstring_parse.polish import \
    create_new_element_doc, fu,fau, fu_t, fau_t, enormer
from codemend import relative_path

elem_lookup = {}  # [elem_id] = elem_doc

# Import pre-computed elem docs
with open(relative_path(
      'docstring_parse/doc_polished/elem_docs.csv'
      # this file is generated by docstring_parse/polish.py
      ), 'rb') as csvfile:
  reader = csv.reader(csvfile)

  columns = tuple(next(reader))
  assert ElemDoc._fields == columns

  for elem in imap(ElemDoc._make, reader):
    elem_id = elem.elem_id
    elem_lookup[elem_id] = elem

# Create children_lookup
children_lookup = defaultdict(list)  # [parent_elem_id] = [elems]
for elem in elem_lookup.values():
  if elem.parent_id:
    children_lookup[elem.parent_id].append(elem)
children_lookup = dict(children_lookup)

def get_training_doc(elem_id, with_parents):
  """
  For bimodal training.
  """
  docs = []
  if elem_id in elem_lookup:
    elemdoc = elem_lookup[elem_id]
    if elemdoc.utter:
      docs.append(elemdoc.utter)
      docs.append(elemdoc.name)
    if with_parents:
      for parent_id in find_parents(elem_id):
        if parent_id in elem_lookup:
          parentdoc = elem_lookup[parent_id]
          if parentdoc.utter:
            docs.append(parentdoc.utter)
            docs.append(parentdoc.name)
  return ' '.join(docs)

def find_elem(elem_id):
  if elem_id in elem_lookup:
    return elem_lookup[elem_id]
  else:
    return None

def find_children(elem_id):
  """
  Find all elements whose parent_id matches this.

  Returns a list of ElemDoc instances.

  """
  if elem_id in children_lookup:
    return children_lookup[elem_id]
  return []

def find_parents(elem_id):
  """
  Returns a list of elem_ids representing parent and ancestors. The returned
  elements are not guaranteed to exist.

  """
  out = []
  while True:
    elem = find_elem(elem_id)
    if not elem: break
    if not elem.parent_id: break
    elem_id = elem.parent_id
    out.append(elem_id)
  return out

# create func_guess_lookup
func_guess_lookup = {}  # [func_name] = elem
for elem in elem_lookup.values():
  if elem.type == 'func':
    func_name = elem.elem_id.split('.')[-1]
    if func_name not in func_guess_lookup or \
       elem.count > func_guess_lookup[func_name].count:
      func_guess_lookup[func_name] = elem

def guess_func_elem_id(func_name):
  """
  Returns the most popular elem_id that has this func_name.

  """
  if func_name in func_guess_lookup:
    return func_guess_lookup[func_name].elem_id
  else:
    return None

def is_positional_argument(elem_id):
  if not '@' in elem_id: return False
  fields = elem_id.split('@', 1)
  if not fields[1]: return False
  return fields[1][0] in string.digits

if __name__ == '__main__':
  print get_training_doc('plt.title', True)
  print get_training_doc('plt.title@bbox', True)
  print get_training_doc('plt.title@bbox@pad', True)
# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A class for parsing a resource projection expression."""

import re

from googlecloudsdk.core.resource import resource_exceptions
from googlecloudsdk.core.resource import resource_filter
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_projection_spec
from googlecloudsdk.third_party.py27 import py27_copy as copy


class Parser(object):
  """Resource projection expression parser.

  A projection is an expression string that contains a list of resource keys
  with optional attributes. This class parses a projection expression into
  resource key attributes and a tree data structure that is used by a projector.

  A projector is a method that takes a JSON-serializable object and a
  projection as input and produces a new JSON-serializable object containing
  only the values corresponding to the keys in the projection. Optional
  projection key attributes may transform the values in the resulting
  JSON-serializable object.

  In the Cloud SDK projection attributes are used for output formatting.

  A default or empty projection expression still produces a projector that
  converts a resource to a JSON-serializable object.

  Attributes:
    __key_attributes_only: Parse projection key list for attributes only.
    _projection: The resource_projection_spec.ProjectionSpec to parse into.
    _root: The projection _Tree tree root node.
    _snake_headings: Dict used to disambiguate key attribute labels.
    _snake_re: Compiled re for converting key names to angry snake case.
  """

  _BOOLEAN_ATTRIBUTES = ['reverse']

  def __init__(self, defaults=None, symbols=None, aliases=None, compiler=None):
    """Constructor.

    Args:
      defaults: resource_projection_spec.ProjectionSpec defaults.
      symbols: Transform function symbol table dict indexed by function name.
      aliases: Resource key alias dictionary.
      compiler: The projection compiler method for nested projections.
    """
    self.__key_attributes_only = False
    self._projection = resource_projection_spec.ProjectionSpec(
        defaults=defaults, symbols=symbols, aliases=aliases, compiler=compiler)
    self._snake_headings = {}
    self._snake_re = None

  class _Tree(object):
    """Defines a Projection tree node.

    Attributes:
      tree: Projection _Tree node indexed by key path.
      attribute: Key _Attribute.
    """

    def __init__(self, attribute):
      self.tree = {}
      self.attribute = attribute

  class _Attribute(object):
    """Defines a projection key attribute.

    Attribute semantics, except transform, are caller defined.  e.g., the table
    formatter uses the label attribute for the column heading for the key.

    Attributes:
      flag: The projection algorithm flag, one of DEFAULT, INNER, PROJECT.
      order: The column sort order, None if not ordered. Lower values have
        higher sort precedence.
      label: A string associated with each projection key.
      reverse: Reverse column sort if True.
      align: The column alignment name: left, center, or right.
      transform: obj = func(obj,...) function applied during projection.
      subformat: Sub-format string.
      hidden: Attribute is projected but not displayed.
    """

    def __init__(self, flag):
      self.flag = flag
      self.order = None
      self.label = None
      self.reverse = None
      self.hidden = False
      self.align = resource_projection_spec.ALIGN_DEFAULT
      self.transform = None
      self.subformat = None

    def __str__(self):
      return (
          '({flag}, {order}, {label}, {align}, {active},'
          ' {transform})'.format(
              flag=self.flag,
              order=('UNORDERED' if self.order is None else str(self.order)),
              label=repr(self.label),
              align=self.align,
              active=self.transform.active if self.transform else None,
              transform=self.transform))

  def _AngrySnakeCase(self, key):
    """Returns an ANGRY_SNAKE_CASE string representation of a parsed key.

    Args:
        key: A parsed resource key.

    Returns:
      The ANGRY_SNAKE_CASE string representation of key, adding components
        from right to left to disambiguate from previous ANGRY_SNAKE_CASE
        strings.
    """
    if self._snake_re is None:
      self._snake_re = re.compile('((?<=[a-z0-9])[A-Z]+|(?!^)[A-Z](?=[a-z]))')
    label = ''
    for index in reversed(key):
      if isinstance(index, basestring):
        key_snake = self._snake_re.sub(r'_\1', index).upper()
        if label:
          label = key_snake + '_' + label
        else:
          label = key_snake
        if label not in self._snake_headings:
          self._snake_headings[label] = 1
          break
    return label

  def _AddKey(self, key, attribute_add):
    """Propagates default attribute values and adds key to the projection.

    Args:
      key: The parsed key to add.
      attribute_add: Parsed _Attribute to add.
    """
    projection = self._root

    # Add or update the inner nodes.
    for name in key[:-1]:
      tree = projection.tree
      if name in tree:
        attribute = tree[name].attribute
        if attribute.flag != self._projection.PROJECT:
          attribute.flag = self._projection.INNER
      else:
        tree[name] = self._Tree(self._Attribute(self._projection.INNER))
      projection = tree[name]

    # Add or update the terminal node.
    tree = projection.tree
    # self.key == [] => . or a function on the entire object.
    name = key[-1] if key else ''
    name_in_tree = name in tree
    if name_in_tree:
      # Already added.
      if (not self.__key_attributes_only and
          any([col for col in self._projection.Columns() if col.key == key])):
        # A duplicate column. A projection can only have one attribute object
        # per key. The first <key, attribute> pair added to the current set of
        # columns remains in the projection. Projection columns may have
        # duplicate keys (e.g., table columns with the same key but different
        # transforms). The attribute copy, with attribute_add merged in, is
        # added to the projection columns but not the projection tree.
        attribute = copy.copy(tree[name].attribute)
      else:
        attribute = tree[name].attribute
      attribute.hidden = False
    elif isinstance(name, (int, long)) and None in tree:
      # New projection for explicit name using slice defaults.
      tree[name] = copy.deepcopy(tree[None])
      attribute = tree[name].attribute
    else:
      # New projection.
      attribute = attribute_add
      if self.__key_attributes_only and attribute.order:
        attribute.hidden = True
      if key or attribute.transform:
        tree[name] = self._Tree(attribute)

    # Propagate non-default values from attribute_add to attribute.
    if attribute_add.order is not None:
      attribute.order = attribute_add.order
    if attribute_add.label is not None:
      attribute.label = attribute_add.label
    elif attribute.label is None:
      attribute.label = self._AngrySnakeCase(key)
    if attribute_add.align != resource_projection_spec.ALIGN_DEFAULT:
      attribute.align = attribute_add.align
    if attribute_add.reverse is not None:
      attribute.reverse = attribute_add.reverse
    elif attribute.reverse is None:
      attribute.reverse = False
    if attribute_add.transform:
      attribute.transform = attribute_add.transform
    if attribute_add.subformat:
      attribute.subformat = attribute_add.subformat
    self._projection.AddAlias(attribute.label, key)

    if not self.__key_attributes_only or attribute.hidden:
      # This key is in the projection.
      attribute.flag = self._projection.PROJECT
      self._projection.AddKey(key, attribute)
    elif not name_in_tree:
      # This is a new attributes only key.
      attribute.flag = self._projection.DEFAULT

  def _ParseKeyAttributes(self, key, attribute):
    """Parses one or more key attributes and adds them to attribute.

    The initial ':' has been consumed by the caller.

    Args:
      key: The parsed key name of the attributes.
      attribute: Add the parsed transform to this resource_projector._Attribute.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.
    """
    while True:
      name = self._lex.Token('=:,)', space=False)
      here = self._lex.GetPosition()
      if self._lex.IsCharacter('=', eoi_ok=True):
        boolean_value = False
        value = self._lex.Token(':,)', space=False, convert=True)
      else:
        boolean_value = True
        if name.startswith('no-'):
          name = name[3:]
          value = False
        else:
          value = True
      if name in self._BOOLEAN_ATTRIBUTES:
        if not boolean_value:
          # A Boolean attribute with a non-Boolean value.
          raise resource_exceptions.ExpressionSyntaxError(
              'value not expected [{0}].'.format(self._lex.Annotate(here)))
      elif boolean_value:
        # A non-Boolean attribute without a value or a no- prefix.
        raise resource_exceptions.ExpressionSyntaxError(
            'value expected [{0}].'.format(self._lex.Annotate(here)))
      if name == 'alias':
        if not value:
          raise resource_exceptions.ExpressionSyntaxError(
              'Cannot unset alias [{0}].'.format(self._lex.Annotate(here)))
        self._projection.AddAlias(value, key)
      elif name == 'align':
        if value not in resource_projection_spec.ALIGNMENTS:
          raise resource_exceptions.ExpressionSyntaxError(
              'Unknown alignment [{0}].'.format(self._lex.Annotate(here)))
        attribute.align = value
      elif name == 'format':
        attribute.subformat = value or ''
      elif name == 'label':
        attribute.label = value or ''
      elif name == 'reverse':
        attribute.reverse = value
      elif name == 'sort':
        attribute.order = value
      else:
        raise resource_exceptions.ExpressionSyntaxError(
            'Unknown key attribute [{0}].'.format(self._lex.Annotate(here)))
      if not self._lex.IsCharacter(':'):
        break

  def _ParseKey(self):
    """Parses a key and optional attributes from the expression.

    Transform functions and key attributes are also handled here.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.

    Returns:
      The parsed key.
    """
    key = self._lex.Key()
    attribute = self._Attribute(self._projection.PROJECT)
    if self._lex.IsCharacter('(', eoi_ok=True):
      func_name = key.pop()
      attribute.transform = self._lex.Transform(func_name,
                                                self._projection.active)
      func_name = attribute.transform.Name()
    else:
      func_name = None
    self._lex.SkipSpace()
    if self._lex.IsCharacter(':'):
      self._ParseKeyAttributes(key, attribute)
    if attribute.transform and attribute.transform.conditional:
      # Parse and evaluate if() transform conditional expression,
      conditionals = self._projection.symbols.get('__conditionals__')

      def GlobalRestriction(key):
        return getattr(conditionals, key, None)

      defaults = resource_projection_spec.ProjectionSpec(
          symbols={'global': GlobalRestriction})
      if not resource_filter.Compile(attribute.transform.conditional,
                                     defaults=defaults).Evaluate(conditionals):
        return
    if func_name and attribute.label is None and not key:
      attribute.label = self._AngrySnakeCase([func_name])
    self._AddKey(key, attribute)

  def _ParseKeys(self):
    """Parses a comma separated list of keys.

    The initial '(' has already been consumed by the caller.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.
    """
    if self._lex.IsCharacter(')'):
      # An empty projection is OK.
      return
    while True:
      self._ParseKey()
      self._lex.SkipSpace()
      if self._lex.IsCharacter(')'):
        break
      if not self._lex.IsCharacter(','):
        raise resource_exceptions.ExpressionSyntaxError(
            'Expected ) in projection expression [{0}].'.format(
                self._lex.Annotate()))

  def _ParseAttributes(self):
    """Parses a comma separated [no-]name[=value] projection attribute list.

    The initial '[' has already been consumed by the caller.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.
    """
    while True:
      name = self._lex.Token('=,])', space=False)
      if name:
        if self._lex.IsCharacter('='):
          value = self._lex.Token(',])', space=False, convert=True)
        else:
          value = 1
        self._projection.AddAttribute(name, value)
        if name.startswith('no-'):
          self._projection.DelAttribute(name[3:])
        else:
          self._projection.DelAttribute('no-' + name)
      if self._lex.IsCharacter(']'):
        break
      if not self._lex.IsCharacter(','):
        raise resource_exceptions.ExpressionSyntaxError(
            'Expected ] in attribute list [{0}].'.format(self._lex.Annotate()))

  def Parse(self, expression=None):
    """Parse a projection expression.

    An empty projection is OK.

    Args:
      expression: The resource projection expression string.

    Raises:
      ExpressionSyntaxError: The expression has a syntax error.

    Returns:
      A ProjectionSpec for the expression.
    """
    self._root = self._projection.GetRoot()
    if not self._root:
      self._root = self._Tree(self._Attribute(self._projection.DEFAULT))
      self._projection.SetRoot(self._root)
    self._projection.SetEmpty(
        self._Tree(self._Attribute(self._projection.PROJECT)))
    if expression:
      self._lex = resource_lex.Lexer(expression, self._projection)
      defaults = False
      self.__key_attributes_only = False
      while self._lex.SkipSpace():
        if self._lex.IsCharacter('('):
          if not self.__key_attributes_only:
            defaults = False
            self._projection.Defaults()
          self._ParseKeys()
        elif self._lex.IsCharacter('['):
          self._ParseAttributes()
        elif self._lex.IsCharacter(':'):
          self.__key_attributes_only = True
        else:
          self.__key_attributes_only = False
          here = self._lex.GetPosition()
          name = self._lex.Token(':([')
          if not name.isalpha():
            raise resource_exceptions.ExpressionSyntaxError(
                'Name expected [{0}].'.format(self._lex.Annotate(here)))
          self._projection.SetName(name)
          defaults = True
      self._lex = None
      if defaults:
        self._projection.Defaults()
    return self._projection


def Parse(expression, defaults=None, symbols=None, aliases=None, compiler=None):
  """Parses a resource projector expression.

  Args:
    expression: The resource projection expression string.
    defaults: resource_projection_spec.ProjectionSpec defaults.
    symbols: Transform function symbol table dict indexed by function name.
    aliases: Resource key alias dictionary.
    compiler: The projection compiler method for nested projections.

  Returns:
    A ProjectionSpec for the expression.
  """
  return Parser(defaults=defaults, symbols=symbols, aliases=aliases,
                compiler=compiler).Parse(expression)
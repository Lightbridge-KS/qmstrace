"""C# source, parsed once into the few facts the C# extractors read (ADR-0004).

The only module that imports tree-sitter: everything else in `extract/csharp/` sees plain,
frozen values — types with their namespace, enclosing types, bases and leading `///` comment;
methods with their attributes and the arguments of each; every comment. A parse error is
`Source.error` only when it falls inside something the extractors read — a type, a method or an
attribute, a test attribute's text, a doc comment's field line; syntax the grammar does not know
elsewhere (a newer language feature) does not stop the file being read.

Implements: DSN-QMT-15
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

import tree_sitter_c_sharp
from tree_sitter import Language, Node, Parser

_PARSER: Final = Parser(Language(tree_sitter_c_sharp.language()))
_TYPES: Final = {
    "class_declaration": "class",
    "record_declaration": "record",
    "struct_declaration": "struct",
    "interface_declaration": "interface",
}
_CONDITIONAL: Final = {"preproc_if", "preproc_elif", "preproc_else"}
_LITERALS: Final = {"string_literal", "verbatim_string_literal", "raw_string_literal"}
# What makes an unreadable span matter: a test attribute or a doc comment's field line in it.
_READ_TEXT: Final = re.compile(r"\[\s*(?:\w+\.)*\w*(?:Fact|Theory)\b|^\s*///.*\w+:", re.M)
_ESCAPES: Final = {'\\"': '"', "\\\\": "\\", "\\'": "'", "\\n": "\n", "\\t": "\t", "\\0": "\0"}


@dataclass(frozen=True, slots=True)
class Argument:
    """One attribute argument: its name when named (`DisplayName = …`), the kind of its value,
    and the value itself when that is a plain string literal — regular, verbatim or raw."""

    name: str | None
    kind: str
    value: str | None
    line: int


@dataclass(frozen=True, slots=True)
class Attribute:
    """One attribute as written: `Fact`, `Xunit.FactAttribute`, `Trait`."""

    name: str
    arguments: tuple[Argument, ...]
    line: int


@dataclass(frozen=True, slots=True)
class Method:
    """One method: its attributes, the text its digest covers (comments left out), and whether
    it sits inside conditional compilation, where it may never be built."""

    name: str
    line: int
    attributes: tuple[Attribute, ...]
    digest_text: str
    conditional: bool


@dataclass(frozen=True, slots=True)
class TypeDecl:
    """One class, record, struct or interface, nested ones included, in source order."""

    name: str
    kind: str
    namespace: str
    outer: tuple[str, ...]  # the enclosing types, outermost first
    bases: tuple[str, ...]  # simple names in the base list, type arguments left out
    abstract: bool
    line: int
    doc: tuple[tuple[int, str], ...]  # the leading `///` lines: number and text after `///`
    methods: tuple[Method, ...]


@dataclass(frozen=True, slots=True)
class Comment:
    """One comment: its first line, its text, and whether it is a `///` doc comment."""

    line: int
    text: str
    doc: bool


@dataclass(frozen=True, slots=True)
class Source:
    """What one file says, as the C# extractors read it."""

    types: tuple[TypeDecl, ...]
    comments: tuple[Comment, ...]
    error: tuple[int, str] | None
    digest_text: str  # the file's tokens, ordinary comments left out, doc comments kept


def parse(text: str) -> Source:
    """Parse one file's text. Never raises for the user's source."""
    tree = _PARSER.parse(text.encode("utf-8"))
    root = tree.root_node
    types: list[TypeDecl] = []
    _declarations(root, "", (), False, types)
    comments = tuple(
        Comment(node.start_point[0] + 1, _text(node), _text(node).startswith("///"))
        for node in _walk(root)
        if node.type == "comment"
    )
    return Source(tuple(types), comments, _first_error(root), _tokens(root, keep_doc=True))


def _declarations(
    node: Node, namespace: str, outer: tuple[str, ...], conditional: bool, found: list[TypeDecl]
) -> None:
    """Every type declared under `node`, with the namespace and enclosing types in force."""
    for child in node.named_children:
        if child.type == "file_scoped_namespace_declaration":
            namespace = _name(child)  # it applies to the declarations that follow it
            _declarations(child, namespace, outer, conditional, found)
        elif child.type == "namespace_declaration":
            inner = ".".join(p for p in (namespace, _name(child)) if p)
            body = child.child_by_field_name("body")
            if body is not None:
                _declarations(body, inner, outer, conditional, found)
        elif child.type in _TYPES:
            _type(child, namespace, outer, conditional, found)
        elif child.type in _CONDITIONAL or child.type == "declaration_list":
            _declarations(child, namespace, outer, conditional or child.type in _CONDITIONAL, found)


def _type(
    node: Node, namespace: str, outer: tuple[str, ...], conditional: bool, found: list[TypeDecl]
) -> None:
    name = _name(node)
    modifiers = {_text(m) for m in node.named_children if m.type == "modifier"}
    bases = tuple(
        _simple(base)
        for b in node.named_children
        if b.type == "base_list"
        for base in b.named_children
    )
    body = node.child_by_field_name("body")
    methods: list[Method] = []
    position = len(found)
    found.append(  # placeholder keeps source order: a type before the types nested in it
        TypeDecl(
            name, _TYPES[node.type], namespace, outer, bases, "abstract" in modifiers, 0, (), ()
        )
    )
    if body is not None:
        _members(body, namespace, (*outer, name), conditional, methods, found)
    found[position] = TypeDecl(
        name,
        _TYPES[node.type],
        namespace,
        outer,
        bases,
        "abstract" in modifiers,
        node.start_point[0] + 1,
        _leading_doc(node),
        tuple(methods),
    )


def _members(
    body: Node,
    namespace: str,
    outer: tuple[str, ...],
    conditional: bool,
    methods: list[Method],
    found: list[TypeDecl],
) -> None:
    for member in body.named_children:
        if member.type == "method_declaration":
            methods.append(
                Method(
                    _name(member),
                    member.start_point[0] + 1,
                    tuple(
                        _attribute(a)
                        for group in member.named_children
                        if group.type == "attribute_list"
                        for a in group.named_children
                        if a.type == "attribute"
                    ),
                    _tokens(member, keep_doc=False),
                    conditional,
                )
            )
        elif member.type in _TYPES:
            _type(member, namespace, outer, conditional, found)
        elif member.type in _CONDITIONAL:
            _members(member, namespace, outer, True, methods, found)


def _attribute(node: Node) -> Attribute:
    name_node = node.child_by_field_name("name")
    name = _text(name_node) if name_node is not None else _text(node).split("(", 1)[0]
    arguments: list[Argument] = []
    for group in node.named_children:
        if group.type != "attribute_argument_list":
            continue
        for argument in group.named_children:
            if argument.type == "attribute_argument":
                arguments.append(_argument(argument))
    return Attribute(name, tuple(arguments), node.start_point[0] + 1)


def _argument(node: Node) -> Argument:
    """`DisplayName = "…"` is named; `"verifies"` is positional."""
    parts = node.children
    named = len(parts) >= 3 and parts[0].type == "identifier" and _text(parts[1]) in ("=", ":")
    value = parts[2] if named else (node.named_children[0] if node.named_children else node)
    return Argument(
        _text(parts[0]) if named else None,
        value.type,
        _literal(value) if value.type in _LITERALS else None,
        node.start_point[0] + 1,
    )


def _literal(node: Node) -> str:
    text = _text(node)
    if node.type == "verbatim_string_literal":
        return text[2:-1].replace('""', '"')
    if node.type == "raw_string_literal":
        return "".join(_text(c) for c in node.children if c.type == "raw_string_content")
    inner = text[1:-1]
    return re.sub(r"\\.", lambda m: _ESCAPES.get(m.group(), m.group()), inner)


def _leading_doc(node: Node) -> tuple[tuple[int, str], ...]:
    """The `///` lines right before a declaration, closest last, in source order."""
    lines: list[tuple[int, str]] = []
    expected = node.start_point[0]  # the line the comment just above must end on
    previous = node.prev_named_sibling
    while previous is not None and previous.type == "comment":
        text = _text(previous)
        if not text.startswith("///") or previous.end_point[0] + 1 != expected:
            break
        lines.append((previous.start_point[0] + 1, text[3:]))
        expected = previous.start_point[0]
        previous = previous.prev_named_sibling
    return tuple(reversed(lines))


def _first_error(root: Node) -> tuple[int, str] | None:
    """The first span the grammar could not read that holds something the extractors read."""
    for node in _walk(root):
        if not (node.is_error or node.is_missing):
            continue
        holder = node.parent
        read_inside = any(
            n.type in ("method_declaration", "attribute_list", *_TYPES) for n in _walk(node)
        )
        while holder is not None and holder.type not in ("method_declaration", "attribute_list"):
            holder = holder.parent
        attributed = holder is not None and (
            holder.type == "attribute_list"
            or any(c.type == "attribute_list" for c in holder.named_children)
        )
        if read_inside or attributed or _READ_TEXT.search(_text(node)):
            what = "a missing token" if node.is_missing else "syntax this C# grammar cannot read"
            return node.start_point[0] + 1, what
    return None


def _tokens(node: Node, *, keep_doc: bool) -> str:
    """The text a digest covers: every token, ordinary comments left out."""
    words: list[str] = []
    for leaf in _walk(node):
        if leaf.type == "comment":
            if keep_doc and _text(leaf).startswith("///"):
                words.append(_text(leaf))
            continue
        if leaf.child_count == 0:
            words.append(_text(leaf))
    return " ".join(words)


def _walk(node: Node) -> list[Node]:
    found: list[Node] = []
    stack = [node]
    while stack:
        current = stack.pop()
        found.append(current)
        stack.extend(reversed(current.children))
    return found


def _name(node: Node) -> str:
    name = node.child_by_field_name("name")
    return _text(name) if name is not None else ""


def _simple(node: Node) -> str:
    """`Base`, `Base<T>`, `Ns.Base` → `Base`."""
    if node.type == "generic_name":
        first = node.named_children[0] if node.named_children else node
        return _text(first)
    if node.type == "qualified_name":
        return _simple(node.named_children[-1]) if node.named_children else _text(node)
    return _text(node)


def _text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8")

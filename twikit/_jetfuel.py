"""
Decoder for "Jetfuel", X's server-driven UI (``/i/jfapi/...``).

The response body is a raw binary document served as ``text/plain``
(verified live 2026-10-23; a HAR export shows it base64-encoded, which is
what :meth:`JetfuelDocument.decode_base64` is for). It is a sequence of
frames, each ``u32 LE length + payload``. The first byte of a payload is
the message kind (0 = dom_data, 1 = dom_ready, 2 = action); dom_data is
``elements + props + timestamp``. Elements hold indexes into the prop array,
children are indexes into the element array, and the last element is the
page root. The layout mirrors ``decodeMessage`` in the web client's
``jetfuel.*.js`` (2026-10, ``x-jf-v: JP-5``).
"""
from __future__ import annotations

import base64
import binascii
import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Callable, Iterator, TypeVar

from .errors import TwitterException

T = TypeVar('T')


class PropKind(IntEnum):
    STR = 0
    INT = 1
    MODS = 3
    ID = 4
    F64 = 5
    BOOL = 6
    ELEMENT = 7
    ELEMENTS = 8
    ENUM = 10
    URL = 11
    RICH_TEXT = 12
    NOT_FOUND = 13
    DATE = 14
    SCRIBE = 15
    BAG = 16
    STR_DICT = 17
    ATOM = 18
    ACTION = 19
    LIST = 21
    PREDICATE = 22
    FEED = 24
    CONDITIONAL_MODS = 25
    STR_LIST = 26
    INT_LIST = 27
    F64_LIST = 28
    BOOL_LIST = 29
    FORM = 30
    SUBATOM = 31


class ActionKind(IntEnum):
    CHANGE = 0
    CONFIRM = 1
    MULTI = 2
    POST_REQUEST = 3
    HAPTIC = 4
    PRESENT = 5
    NAVIGATE = 6
    REFRESH = 7
    CACHE_CLEAR = 8
    PREFETCH = 9
    SCRIBE = 10
    SYSTEM = 11
    DELAYED = 12
    AUTH = 13
    ALERT = 14
    FORM_SUBMIT = 15
    FORM_RESET = 16
    FORM_VALIDATE = 17
    FORM_SET_FOCUS = 18
    PRESENT_ROTATABLE = 19
    PRESENT_SHEET = 20
    PRESENT_TOAST = 21


class NavigateKind(IntEnum):
    PAGE = 0
    PAGE_POST = 1
    DISMISS = 2
    BACK = 3
    BACK_ROOT = 4
    SCROLL_TOP = 5
    SCROLL_BOTTOM = 6
    SCROLL_ID = 7
    LINK = 8
    PAGE_RESET_TO = 9


class Ids:
    """
    Known component / prop / icon numbers. Components and props are the low
    16 bits of murmur3_32 (seed 0, UTF-8) of the name; icons are indexes
    into the web client's icon name array.
    """
    # components
    VIEW = 0xe075
    TEXT = 0x9933
    ICON = 0xc4d9
    PAGE = 0xd118
    GRID = 0xf913
    GRID_ROW = 0x2008
    GRID_CELL = 0x3139
    RICH_TEXT = 0x7335       # RichText2
    RICH_TEXT_TEXT = 0x0fbb  # RichText.Text

    # props
    MOD = 0xe940
    TEXT_VALUE = 0xdf4d      # body of Text / RichText.Text
    ICON_KEY = 0x6a44        # key
    SIZE = 0x17fa
    COLUMNS = 0x01bc
    HEADER = 0x4ca9
    LINK = 0xd234
    PAGE_INFO = 0x5729       # str_dict {page, section}

    # icons
    ICON_CHECKMARK_CIRCLE_FILL = 84
    ICON_CLOSE_CIRCLE = 101
    ICON_INFORMATION_CIRCLE = 224


@dataclass(eq=False)
class Element:
    """One element. ``type`` is the low 16 bits of the component name's murmur3 hash."""
    type: int
    props: list[tuple[int, int]]  # (prop name hash, index into the prop array)
    children: list[int]           # indexes into the element array
    id: int | None
    extend: int | None

    def __repr__(self) -> str:
        return f'<JetfuelElement type=0x{self.type:04x} props={len(self.props)} children={len(self.children)}>'


@dataclass(eq=False)
class Prop:
    """A prop value. Kinds that are skipped (atom, predicate, ...) have ``value`` None."""
    kind: PropKind
    value: Any

    def __repr__(self) -> str:
        return f'<JetfuelProp {self.kind.name}={self.value!r}>'


@dataclass(frozen=True)
class Action:
    kind: ActionKind
    navigate: NavigateKind | None
    url_prop: int | None


class JetfuelDocument:
    """A decoded Jetfuel page."""

    def __init__(self, elements: list[Element], props: list[Prop], timestamp: int, root_index: int) -> None:
        #: Elements; the last one is the page root.
        self.elements = elements
        #: Prop values. ``Element.props`` holds indexes into this.
        self.props = props
        #: Server-side generation time (Unix seconds).
        self.timestamp = timestamp
        #: Index of the root element named by dom_ready (the last element if absent).
        self.root_index = root_index

    @property
    def root(self) -> Element:
        return self.elements[self.root_index]

    @classmethod
    def decode_base64(cls, data: str) -> JetfuelDocument:
        """Decodes a body that was stored as base64 (a HAR export, for instance)."""
        try:
            raw = base64.b64decode(data.strip(), validate=True)
        except (binascii.Error, ValueError) as e:
            raise TwitterException('Jetfuel body is not base64: ' + _truncate(data)) from e
        return cls.decode(raw)

    @classmethod
    def decode(cls, data: bytes) -> JetfuelDocument:
        """Decodes a raw response body."""
        elements: list[Element] | None = None
        props: list[Prop] | None = None
        timestamp = 0
        root: int | None = None

        offset = 0
        while len(data) - offset > 4:
            (length,) = struct.unpack_from('<I', data, offset)
            offset += 4
            if len(data) - offset < length:
                raise TwitterException(
                    f'Jetfuel frame of {length} bytes exceeds the {len(data) - offset} bytes left.'
                )
            reader = _Reader(data, offset, length)
            offset += length

            kind = reader.u8()
            if kind == 0:  # dom_data
                elements = reader.list(reader.element)
                props = reader.list(reader.prop)
                timestamp = reader.i32()
                reader.expect_end()
            elif kind == 1:  # dom_ready
                root = reader.index()
                reader.optional(reader.i32)
            elif kind == 2:  # action
                reader.action()
            else:
                raise TwitterException('Unknown Jetfuel message kind.')

        if elements is None or props is None or not elements:
            raise TwitterException('Jetfuel response carries no page (dom_data).')
        if root is None or root < 0 or root >= len(elements):
            root = len(elements) - 1
        return cls(elements, props, timestamp, root)

    # ---------------------------------------------------------------- lookup

    def prop(self, element: Element, key: int) -> Prop | None:
        """The element's prop value for ``key`` (None if absent)."""
        for k, index in element.props:
            if k == key and 0 <= index < len(self.props):
                return self.props[index]
        return None

    def str(self, element: Element, key: int) -> str | None:
        p = self.prop(element, key)
        if p is not None and p.kind in (PropKind.STR, PropKind.URL) and isinstance(p.value, str):
            return p.value
        return None

    def int(self, element: Element, key: int) -> int | None:
        p = self.prop(element, key)
        if (
            p is not None
            and p.kind in (PropKind.INT, PropKind.ENUM, PropKind.ELEMENT)
            and isinstance(p.value, int) and not isinstance(p.value, bool)
        ):
            return p.value
        return None

    def child_elements(self, element: Element) -> Iterator[Element]:
        for child in element.children:
            if 0 <= child < len(self.elements):
                yield self.elements[child]

    def descendants(self, element: Element) -> Iterator[Element]:
        """All elements below ``element``, depth first (repeated if shared by several parents)."""
        for e in self.child_elements(element):
            yield e
            yield from self.descendants(e)

    def self_and_descendants(self, element: Element) -> Iterator[Element]:
        yield element
        yield from self.descendants(element)


def _truncate(s: str) -> str:
    return s if len(s) <= 80 else s[:80] + '...'


class _Reader:
    def __init__(self, data: bytes, offset: int, length: int) -> None:
        self._b = data
        self._p = offset
        self._end = offset + length

    def _need(self, n: int) -> None:
        if self._end - self._p < n:
            raise TwitterException('Jetfuel frame ended early.')

    def expect_end(self) -> None:
        if self._p != self._end:
            raise TwitterException(f'Jetfuel dom_data left {self._end - self._p} undecoded bytes.')

    def u8(self) -> int:
        self._need(1)
        v = self._b[self._p]
        self._p += 1
        return v

    def bool(self) -> bool:
        return self.u8() != 0

    def uint(self) -> int:
        """LEB128 unsigned varint."""
        result = 0
        shift = 0
        while True:
            c = self.u8()
            if shift < 64:
                result |= (c & 0x7f) << shift
            shift += 7
            if c < 0x80:
                return result

    def index(self) -> int:
        """A varint that should fit an index into the element / prop arrays."""
        v = self.uint()
        return -1 if v > 0x7fffffff else v

    def _unpack(self, fmt: str, size: int) -> Any:
        self._need(size)
        (v,) = struct.unpack_from(fmt, self._b, self._p)
        self._p += size
        return v

    def i16(self) -> int:
        return self._unpack('<h', 2)

    def u16(self) -> int:
        return self._unpack('<H', 2)

    def i32(self) -> int:
        return self._unpack('<i', 4)

    def i64(self) -> int:
        return self._unpack('<q', 8)

    def f64(self) -> float:
        return self._unpack('<d', 8)

    def str(self) -> str:
        n = self.index()
        if n < 0:
            raise TwitterException('Jetfuel string length overflow.')
        self._need(n)
        s = self._b[self._p:self._p + n].decode('utf-8')
        self._p += n
        return s

    def list(self, item: Callable[[], T]) -> list[T]:
        n = self.index()
        if n < 0 or n > self._end - self._p:
            raise TwitterException('Jetfuel list length overflow.')
        return [item() for _ in range(n)]

    def optional(self, item: Callable[[], T]) -> T | None:
        return item() if self.bool() else None

    def map(self, key: Callable[[], Any], value: Callable[[], Any]) -> list[tuple[Any, Any]]:
        return self.list(lambda: (key(), value()))

    def element(self) -> Element:
        type_ = self.u16()
        props = self.map(self.u16, self.index)
        children = self.list(self.index)
        id_ = self.optional(self.i64)
        extend = self.optional(self.index)
        return Element(type_, props, children, id_, extend)

    def prop(self) -> Prop:
        raw_kind = self.u8()
        try:
            kind = PropKind(raw_kind)
        except ValueError:
            raise TwitterException(f'Unknown Jetfuel prop kind {raw_kind}.') from None

        value: Any
        if kind in (PropKind.STR, PropKind.URL):
            value = self.str()
        elif kind == PropKind.INT:
            value = self.i32()
        elif kind == PropKind.MODS:
            value = self._mods()
        elif kind == PropKind.CONDITIONAL_MODS:
            self.list(lambda: (self._mods(), self._predicate()))
            value = None
        elif kind in (PropKind.ID, PropKind.DATE):
            value = self.i64()
        elif kind == PropKind.F64:
            value = self.f64()
        elif kind == PropKind.BOOL:
            value = self.bool()
        elif kind in (PropKind.ELEMENT, PropKind.ENUM, PropKind.SCRIBE):
            value = self.index()
        elif kind in (PropKind.ELEMENTS, PropKind.LIST, PropKind.FEED):
            value = self.list(self.index)
        elif kind == PropKind.RICH_TEXT:
            value = self.list(lambda: (self.u8(), self.str(), self.str() if self.bool() else None))
        elif kind == PropKind.BAG:
            value = self.map(self.i16, self.index)
        elif kind == PropKind.STR_DICT:
            value = self._str_dict()
        elif kind == PropKind.ATOM:
            self._ref()
            self.index()
            self.bool()
            value = None
        elif kind == PropKind.SUBATOM:
            self._ref()
            value = None
        elif kind == PropKind.ACTION:
            value = self.action()
        elif kind == PropKind.PREDICATE:
            self._predicate()
            value = None
        elif kind == PropKind.STR_LIST:
            value = self.list(self.str)
        elif kind == PropKind.INT_LIST:
            value = self.list(self.i32)
        elif kind == PropKind.F64_LIST:
            value = self.list(self.f64)
        elif kind == PropKind.BOOL_LIST:
            value = self.list(self.bool)
        elif kind == PropKind.FORM:
            self.str()
            self._str_dict()
            self._str_dict()
            self.str()
            self.u8()
            value = None
        elif kind == PropKind.NOT_FOUND:
            value = None
        else:  # pragma: no cover - every member is handled above
            raise TwitterException(f'Unknown Jetfuel prop kind {raw_kind}.')
        return Prop(kind, value)

    def _mods(self) -> list[list[int]]:
        return self.list(lambda: self.list(self.i32))

    def _str_dict(self) -> dict[str, str]:
        return dict(self.map(self.str, self.str))

    def _ref(self) -> None:
        """A reference to an atom / bag_key / form_field etc. Skipped - the value is not needed."""
        kind = self.u8()
        if kind == 0:                       # atom
            self.i64()
        elif kind == 4:                     # atom_with_root
            self.i64()
            self.index()
        elif kind == 1:                     # bag_key
            self.i16()
            self.index()
        elif kind in (2, 3, 7, 8):          # str_key, url_param, form_field, form_field_error
            self.str()
            self.index()
        elif kind in (5, 6, 9, 10, 11):     # transforming_*, form_submission_status, form_submit_url, form_values
            self.index()
        else:
            raise TwitterException('Unknown Jetfuel ref kind.')

    def _change(self) -> None:
        kind = self.u8()
        self._ref()
        if kind == 0:                       # null
            pass
        elif kind in (1, 5, 7, 8):          # set, list_remove, merge_bag, merge_str_dict
            self.index()
        elif kind == 2:                     # inc
            self.i16()
        elif kind == 3:                     # str_append
            self.str()
        elif kind == 4:                     # list_insert
            self.index()
            self.optional(self.i16)
        elif kind == 6:                     # toggle
            if self.bool():
                self.index()
                self.index()
        else:
            raise TwitterException('Unknown Jetfuel change kind.')

    def _predicate(self) -> None:
        kind = self.u8()
        if kind in (0, 15):                 # null, not_null
            self._ref()
        elif kind in (1, 2, 5, 6, 7, 8):    # is, is_not, gt, gte, lt, lte
            self._ref()
            self.index()
        elif kind in (3, 4):                # in, not_in
            self._ref()
            self.list(self.index)
        elif kind in (9, 10, 11):           # starts_with, ends_with, includes
            self._ref()
            self.str()
        elif kind in (12, 13):              # and, or
            self._predicate()
            self._predicate()
        elif kind == 14:                    # not
            self._predicate()
        else:
            raise TwitterException('Unknown Jetfuel predicate kind.')

    def action(self) -> Action:
        """An action. Only page navigations (navigate) keep their URL prop number; the rest are skipped."""
        raw_kind = self.u8()
        try:
            kind = ActionKind(raw_kind)
        except ValueError:
            raise TwitterException(f'Unknown Jetfuel action kind {raw_kind}.') from None

        if kind == ActionKind.CHANGE:
            self._change()
        elif kind == ActionKind.CONFIRM:
            self.index()
            self.action()
            if self.bool():
                self.action()
        elif kind == ActionKind.MULTI:
            self.list(self.action)
        elif kind == ActionKind.POST_REQUEST:
            self.index()
            self.index()
            for _ in range(3):
                if self.bool():
                    self.action()
        elif kind == ActionKind.HAPTIC:
            self.action()
            self.i16()
        elif kind == ActionKind.PRESENT:
            self.index()
            self.u8()
        elif kind == ActionKind.PRESENT_TOAST:
            self.index()
            self.i16()
            self.bool()
        elif kind == ActionKind.PRESENT_ROTATABLE:
            self.index()
            self.u8()
            self.bool()
        elif kind == ActionKind.PRESENT_SHEET:
            self.index()
            self.index()
            self.str()
        elif kind == ActionKind.NAVIGATE:
            return self._navigate()
        elif kind == ActionKind.REFRESH:
            self.u8()
            self.optional(self.i64)
        elif kind == ActionKind.CACHE_CLEAR:
            self.str()
        elif kind == ActionKind.PREFETCH:
            self.list(self.str)
            self.u8()
        elif kind == ActionKind.SCRIBE:
            self.str()
            self.index()
        elif kind == ActionKind.SYSTEM:
            self.u8()
            self.index()
        elif kind == ActionKind.DELAYED:
            self.action()
            self.i16()
        elif kind == ActionKind.AUTH:
            self.str()
            self.str()
            self.str()
        elif kind == ActionKind.ALERT:
            self.str()
            if self.bool():
                self.str()
        elif kind == ActionKind.FORM_SUBMIT:
            self.index()
            self.index()
        elif kind == ActionKind.FORM_RESET:
            self.index()
            self.list(self.str)
        elif kind == ActionKind.FORM_VALIDATE:
            self.index()
            self.index()
        elif kind == ActionKind.FORM_SET_FOCUS:
            self.index()
            self.str()
        return Action(kind, None, None)

    def _navigate(self) -> Action:
        raw_kind = self.u8()
        try:
            kind = NavigateKind(raw_kind)
        except ValueError:
            raise TwitterException(f'Unknown Jetfuel navigate kind {raw_kind}.') from None

        url: int | None = None
        if kind in (NavigateKind.PAGE, NavigateKind.PAGE_RESET_TO):
            url = self.index()
            self.optional(self.index)
            self.bool()
        elif kind == NavigateKind.PAGE_POST:
            url = self.index()
            self.optional(self.index)
            self.optional(self.index)
            self.bool()
        elif kind == NavigateKind.LINK:
            url = self.index()
        elif kind == NavigateKind.SCROLL_ID:
            self.index()
        # DISMISS, BACK, BACK_ROOT, SCROLL_TOP, SCROLL_BOTTOM carry nothing.
        return Action(ActionKind.NAVIGATE, kind, url)

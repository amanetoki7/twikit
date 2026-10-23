"""
Creator monetization eligibility (the Creator Studio "eligible / not eligible" pages).
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Iterator

from ._jetfuel import Element, Ids, JetfuelDocument, PropKind


class CreatorProgram(Enum):
    """A creator monetization program."""
    #: Original content rewards (post monetization).
    ORIGINAL_CONTENT_REWARDS = 'original_content_rewards'
    #: Creator subscriptions.
    SUBSCRIPTIONS = 'subscriptions'


class CreatorRequirement:
    """
    One requirement of a creator monetization program.

    Attributes
    ----------
    text : :class:`str`
        The requirement ("Have at least 500 verified followers", ...).
    is_met : :class:`bool`
        Whether the account meets it (checkmark vs. cross icon).
    value : :class:`str` | None
        The current value shown next to the progress bar ("136", "26.9K").
        None when the row has no bar.
    progress : :class:`float` | None
        Progress bar ratio (0-1). X rounds it to twentieths, so this is a
        guide, not the exact ratio. None when the row has no bar.
    progress_columns : list[:class:`int`] | None
        Width (``columns``) of each cell of the progress bar; the first is
        the filled part.
    details : list[:class:`str`]
        Other text found in the row.
    notes : list[:class:`str`]
        Notes attached to the row ("Replies are not included", ...).
    """

    def __init__(
        self,
        text: str,
        is_met: bool,
        value: str | None,
        progress: float | None,
        progress_columns: list[int] | None,
        details: list[str],
        notes: list[str]
    ) -> None:
        self.text = text
        self.is_met = is_met
        self.value = value
        self.progress = progress
        self.progress_columns = progress_columns
        self.details = details
        self.notes = notes

    def __repr__(self) -> str:
        value = '' if self.value is None else f' value={self.value}'
        return f'<CreatorRequirement met={self.is_met} "{self.text}"{value}>'


class CreatorEligibility:
    """
    The requirements of a creator monetization program and how far the
    logged-in account has got (the content of Creator Studio's
    "eligible / not eligible" page).

    Attributes
    ----------
    program : :class:`CreatorProgram`
        Which program.
    page : :class:`str` | None
        X's page name (``creators_original_content_rewards``, ...).
    summary : :class:`str` | None
        The text shown above the requirement list ("... you need to meet
        the following requirements:", "Unfortunately ...", ...).
    requirements : list[:class:`CreatorRequirement`]
        The requirements, in page order.
    notes : list[:class:`str`]
        Text outside the requirement list (notes and footer lines).
    help_url : :class:`str` | None
        Link to the Help Center.
    timestamp : :class:`datetime`
        When X generated the page (UTC).
    """

    def __init__(
        self,
        program: CreatorProgram,
        page: str | None,
        summary: str | None,
        requirements: list[CreatorRequirement],
        notes: list[str],
        help_url: str | None,
        timestamp: datetime
    ) -> None:
        self.program = program
        self.page = page
        self.summary = summary
        self.requirements = requirements
        self.notes = notes
        self.help_url = help_url
        self.timestamp = timestamp

    @property
    def is_eligible(self) -> bool:
        """Whether every requirement is met."""
        return bool(self.requirements) and all(r.is_met for r in self.requirements)

    @property
    def unmet(self) -> list[CreatorRequirement]:
        """Only the requirements that are not met."""
        return [r for r in self.requirements if not r.is_met]

    def __repr__(self) -> str:
        met = sum(1 for r in self.requirements if r.is_met)
        return f'<CreatorEligibility program={self.program.name} met={met}/{len(self.requirements)}>'

    # ------------------------------------------------------------ parsing

    @classmethod
    def _from_bytes(cls, program: CreatorProgram, body: bytes) -> CreatorEligibility:
        # Verified live 2026-10-23: the body is the raw binary document
        # (Content-Type text/plain, no base64).
        return cls._from_document(program, JetfuelDocument.decode(body))

    @classmethod
    def _from_document(cls, program: CreatorProgram, doc: JetfuelDocument) -> CreatorEligibility:
        # The page is a sequence of "View (row) -> Icon (checkmark_circle_fill
        # / close_circle) + Text (requirement) [+ Grid (progress bar) + Text
        # (current value)] [+ View (information_circle + Text note)]". A row
        # is "the smallest element holding both a status icon and text"
        # rather than a fixed element type, so nesting changes do not break it.
        root = doc.root
        header = doc.int(root, Ids.HEADER)
        page_info = doc.prop(root, Ids.PAGE_INFO)
        page = page_info.value.get('page') if page_info is not None and isinstance(page_info.value, dict) else None

        requirements: list[CreatorRequirement] = []
        notes: list[str] = []
        summary: str | None = None

        def walk(element: Element, index: int) -> None:
            nonlocal summary
            if index == header:
                return
            if _is_row(doc, element, _is_status_icon):
                requirements.append(_parse_row(doc, element))
                return
            if element.type in (Ids.TEXT, Ids.RICH_TEXT):
                text = _text_of(doc, element)
                if not text.strip():
                    return
                if summary is None and not requirements:
                    summary = text
                else:
                    notes.append(text)
                return
            for child in element.children:
                if 0 <= child < len(doc.elements):
                    walk(doc.elements[child], child)

        walk(root, doc.root_index)

        help_url = next(
            (
                p.value for p in doc.props
                if p.kind == PropKind.URL and isinstance(p.value, str)
                and p.value.lower().startswith('http')
            ),
            None
        )

        return cls(
            program, page, summary, requirements, notes, help_url,
            datetime.fromtimestamp(doc.timestamp, timezone.utc)
        )


def _is_status_icon(doc: JetfuelDocument, e: Element) -> bool:
    return e.type == Ids.ICON and doc.int(e, Ids.ICON_KEY) in (
        Ids.ICON_CHECKMARK_CIRCLE_FILL, Ids.ICON_CLOSE_CIRCLE
    )


def _is_note_icon(doc: JetfuelDocument, e: Element) -> bool:
    return e.type == Ids.ICON and not _is_status_icon(doc, e)


def _has_text(doc: JetfuelDocument, e: Element) -> bool:
    return any(d.type in (Ids.TEXT, Ids.RICH_TEXT) for d in doc.self_and_descendants(e))


def _is_row(
    doc: JetfuelDocument, e: Element, icon: Callable[[JetfuelDocument, Element], bool]
) -> bool:
    """An element holding both an icon (per ``icon``) and text, none of whose children holds both on its own."""
    if not any(icon(doc, d) for d in doc.self_and_descendants(e)) or not _has_text(doc, e):
        return False
    for c in doc.child_elements(e):
        if any(icon(doc, d) for d in doc.self_and_descendants(c)) and _has_text(doc, c):
            return False
    return True


def _parse_row(doc: JetfuelDocument, row: Element) -> CreatorRequirement:
    texts: list[str] = []
    notes: list[str] = []
    icon_key: int | None = None
    columns: list[int] | None = None
    value_index = -1

    def walk(e: Element) -> None:
        nonlocal icon_key, columns, value_index
        if e is not row and _is_row(doc, e, _is_note_icon):
            note = ''.join(
                _text_of(doc, d) for d in doc.self_and_descendants(e)
                if d.type in (Ids.TEXT, Ids.RICH_TEXT)
            )
            if note.strip():
                notes.append(note)
            return
        if icon_key is None and _is_status_icon(doc, e):
            icon_key = doc.int(e, Ids.ICON_KEY)
            return
        if e.type in (Ids.TEXT, Ids.RICH_TEXT):
            text = _text_of(doc, e)
            if text.strip():
                texts.append(text)
            return
        if e.type == Ids.GRID and columns is None:
            columns = [
                doc.int(d, Ids.COLUMNS) or 0
                for d in doc.descendants(e) if d.type == Ids.GRID_CELL
            ]
            value_index = len(texts)
            return
        for child in doc.child_elements(e):
            walk(child)

    walk(row)

    requirement = texts[0] if texts else ''
    value: str | None = None
    if columns is not None and 1 <= value_index < len(texts):
        value = texts[value_index]
    details = [t for t in texts[1:] if t != value]

    progress: float | None = None
    if columns:
        total = sum(columns)
        if total > 0:
            progress = columns[0] / total

    return CreatorRequirement(
        requirement, icon_key == Ids.ICON_CHECKMARK_CIRCLE_FILL,
        value, progress, columns, details, notes
    )


def _text_of(doc: JetfuelDocument, e: Element) -> str:
    if e.type == Ids.RICH_TEXT:
        return ''.join(
            doc.str(d, Ids.TEXT_VALUE) or ''
            for d in doc.descendants(e) if d.type == Ids.RICH_TEXT_TEXT
        )
    return doc.str(e, Ids.TEXT_VALUE) or ''

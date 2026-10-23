"""Community Notes (Birdwatch) contributor profile and rating results.

The note itself is :class:`twikit.tweet.CommunityNote`; this module holds the
objects around it: the contributor profile X shows at
``x.com/i/communitynotes/u/<alias>`` and the acknowledgement X returns when a
note is rated. Shapes were captured from the web client on 2026-10-23.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client.client import Client
    from .tweet import CommunityNote
    from .utils import Result


class CommunityNotesProfile:
    """
    A Community Notes contributor profile (``BirdwatchFetchBirdwatchProfile``),
    merged with the enrollment data X only returns for the logged-in account
    (``BirdwatchFetchAuthenticatedUserProfile``).

    Attributes
    ----------
    alias : :class:`str`
        The contributor alias (``adjective-noun-bird``). Profiles are keyed by
        this, not by the X account.
    is_me : :class:`bool`
        True when this is the logged-in account's own profile; only then are
        the ``can_write_notes`` / enrollment attributes filled in.
    is_top_writer : :class:`bool`
    is_api_contributor : :class:`bool`
        True for AI note writers using the public API.
    has_notes : :class:`bool`
    deleted_notes_count : :class:`int`
    notes_count : :class:`dict`
        Writing statistics: ``awaiting_more_ratings``,
        ``currently_rated_helpful``, ``currently_rated_not_helpful``,
        ``last_updated_at``. X omits a counter that is zero.
    ratings_count : :class:`dict`
        Rating statistics: ``awaiting_more_ratings``,
        ``rated_after_decision``, ``successful`` and ``unsuccessful`` (each
        ``{helpful_count, not_helpful_count, total}``), ``last_updated_at``.
    can_write_notes : :class:`bool` | None
        Whether the account may write notes (own profile only).
    enrollment_state : :class:`str` | None
        ``NewUser``, ``EarnedIn``, ``EarnedOutNoAcknowledge``, ... (own
        profile only).
    successful_rating_needed_to_earn_in : :class:`int` | None
        Rating impact still needed to unlock note writing (own profile only).
    needs_your_help_frequency : :class:`str` | None
        Notification setting for the "needs your help" alerts (own profile
        only).
    enrollment_changed_at : :class:`int` | None
        Unix milliseconds of the last enrollment state change (own profile
        only).
    survey_url : :class:`str` | None
    """

    def __init__(
        self,
        client: Client,
        data: dict,
        authenticated: dict | None = None
    ) -> None:
        self._client = client
        self._data = data
        self._authenticated = authenticated
        self.alias: str = data.get('alias') or (authenticated or {}).get('alias')
        self.is_me: bool = authenticated is not None
        self.is_top_writer: bool = bool(data.get('is_top_writer'))
        self.is_api_contributor: bool = bool(data.get('is_api_contributor'))
        self.has_notes: bool = bool(data.get('has_notes'))
        self.deleted_notes_count: int = data.get('deleted_notes_count') or 0
        self.notes_count: dict = data.get('notes_count') or {}
        self.ratings_count: dict = data.get('ratings_count') or {}

        auth = authenticated or {}
        enrollment = auth.get('user_enrollment') or {}
        self.can_write_notes: bool | None = auth.get('can_write_notes')
        self.enrollment_state: str | None = enrollment.get('enrollment_state')
        self.successful_rating_needed_to_earn_in: int | None = enrollment.get(
            'successful_rating_needed_to_earn_in'
        )
        self.enrollment_changed_at: int | None = enrollment.get(
            'timestamp_of_last_state_change'
        )
        self.survey_url: str | None = enrollment.get('survey_url')
        self.needs_your_help_frequency: str | None = (
            auth.get('notification_settings') or {}
        ).get('needs_your_help_frequency')

    # -- rating impact -------------------------------------------------------

    @property
    def successful_ratings(self) -> int:
        """Ratings that agreed with the status the note ended up with."""
        return (self.ratings_count.get('successful') or {}).get('total') or 0

    @property
    def unsuccessful_ratings(self) -> int:
        """Ratings that went against the status the note ended up with."""
        return (self.ratings_count.get('unsuccessful') or {}).get('total') or 0

    @property
    def ratings_awaiting_more_ratings(self) -> int:
        """Ratings on notes that have no status yet."""
        return self.ratings_count.get('awaiting_more_ratings') or 0

    @property
    def ratings_after_decision(self) -> int:
        """Ratings made after the note already had a status (no impact)."""
        return self.ratings_count.get('rated_after_decision') or 0

    @property
    def rating_impact(self) -> int:
        """
        The "Rating impact" score shown on the profile page.

        Computed the way the web client does it (bundle of 2026-10-23)::

            successful.total
            - unsuccessful.helpful_count
            - 2 * unsuccessful.not_helpful_count

        i.e. a "not helpful" rating on a note that ended up Helpful costs
        twice as much as a "helpful" rating on a note that ended up Not
        Helpful. New contributors need
        :attr:`successful_rating_needed_to_earn_in` (currently 5) to unlock
        writing.
        """
        unsuccessful = self.ratings_count.get('unsuccessful') or {}
        return (
            self.successful_ratings
            - (unsuccessful.get('helpful_count') or 0)
            - 2 * (unsuccessful.get('not_helpful_count') or 0)
        )

    # -- writing impact ------------------------------------------------------

    @property
    def notes_rated_helpful(self) -> int:
        return self.notes_count.get('currently_rated_helpful') or 0

    @property
    def notes_rated_not_helpful(self) -> int:
        return self.notes_count.get('currently_rated_not_helpful') or 0

    @property
    def notes_awaiting_more_ratings(self) -> int:
        return self.notes_count.get('awaiting_more_ratings') or 0

    @property
    def writing_impact(self) -> int:
        """
        The "Writing impact" score shown on the profile page:
        ``currently_rated_helpful - currently_rated_not_helpful`` (same
        formula as the web client).
        """
        return self.notes_rated_helpful - self.notes_rated_not_helpful

    # -- actions -------------------------------------------------------------

    async def get_notes(
        self,
        count: int = 10,
        include_drafts: bool = False,
        cursor: str | None = None
    ) -> Result[CommunityNote]:
        """
        Notes written under this alias.

        See Also
        --------
        Client.get_contributor_community_notes
        """
        return await self._client.get_contributor_community_notes(
            self.alias, count, include_drafts, cursor
        )

    async def update(self) -> None:
        """Re-fetches the profile and refreshes every attribute."""
        new = await self._client.get_community_notes_profile(
            None if self.is_me else self.alias
        )
        self.__dict__.update(new.__dict__)

    def __repr__(self) -> str:
        return (
            f'<CommunityNotesProfile alias="{self.alias}" '
            f'rating_impact={self.rating_impact} '
            f'writing_impact={self.writing_impact}>'
        )

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, CommunityNotesProfile)
            and self.alias == __value.alias
        )

    def __ne__(self, __value: object) -> bool:
        return not self == __value


class CommunityNoteRating:
    """
    The acknowledgement X returns from ``BirdwatchCreateRating``
    (``data.birdwatchnote_rate_v3``).

    Attributes
    ----------
    note_id : :class:`str`
    tweet_id : :class:`str`
    helpfulness_level : :class:`str`
        ``Helpful``, ``SomewhatHelpful`` or ``NotHelpful``.
    helpful_tags : list[:class:`str`]
    not_helpful_tags : list[:class:`str`]
    """

    def __init__(self, note_id: str, tweet_id: str, data: dict) -> None:
        self._data = data
        self.note_id = note_id
        self.tweet_id = tweet_id
        data_v2 = data.get('data_v2') or {}
        self.helpfulness_level: str = data_v2.get('helpfulness_level')
        self.helpful_tags: list[str] = data_v2.get('helpful_tags') or []
        self.not_helpful_tags: list[str] = data_v2.get('not_helpful_tags') or []

    def __repr__(self) -> str:
        return (
            f'<CommunityNoteRating note_id="{self.note_id}" '
            f'helpfulness_level="{self.helpfulness_level}">'
        )

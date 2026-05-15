"""Low-level WordprocessingML helpers for **track changes** (revisions).

These functions build OOXML elements under ``word/document.xml``: mainly ``<w:del>`` (deletion)
and ``<w:ins>`` (insertion). Microsoft Word reads that XML and shows strikethrough, underlines,
balloons, and Accept/Reject actions in the Review UI.

**Consumers**

- ``output_json_to_docx.py`` — builds a reviewed contract from ``output.json`` + ``cpwd.txt``.
- ``main.py`` — optional legacy path for ``cpwd_replacements.txt`` style builds.

**Revision vs comment IDs**

Word uses separate id spaces for revisions and comments. ``REVISION_ID_BASE`` keeps revision
``w:id`` values high enough not to collide with comment ids created earlier in the same story.

**Example (conceptual)**

Calling ``append_tracked_replacement_paragraph(..., original="Old line", suggested="New line", ...)``
appends one ``<w:p>`` whose children are a ``<w:del>`` (showing ``Old line``) and a ``<w:ins>``
(showing ``New line``). After the user clicks **Accept** in Word, typically only ``New line``
remains as normal text.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from docx import Document
from docx.oxml.ns import qn
from docx.oxml.parser import OxmlElement

# First revision id; must stay clear of comment id values in the same document body.
REVISION_ID_BASE = 100_000

# Paragraph children that wrap runs: walk inside these when collecting w:r for comments/anchors.
_INS_DEL = frozenset((qn("w:ins"), qn("w:del")))


def utc_revision_timestamp() -> str:
    """UTC timestamp in ISO-like form required on ``w:del`` / attributes.

    **Returns:** String like ``2026-03-24T12:00:00Z``.

    **Example:** Stored as ``w:date`` so Word shows “time of edit” in review metadata.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_track_revisions(doc: Document) -> None:
    """Turn on “track revisions” in document settings if not already set.

    **Effect:** Adds ``<w:trackRevisions w:val="true"/>`` under ``settings.xml`` when missing.

    **Why:** Without it, some Word builds still show changes, but behavior is more consistent when
    the flag matches a human-edited “Track Changes on” document.

    **Args:**
        doc: The python-docx ``Document`` being built.
    """
    settings_elm = doc.settings._element
    if settings_elm.find(qn("w:trackRevisions")) is not None:
        return
    settings_elm.append(OxmlElement("w:trackRevisions", attrs={qn("w:val"): "true"}))


def new_rsid() -> str:
    """Random 8-hex revision save id (``w:rsid*`` attributes).

    **Returns:** Uppercase hex string, e.g. ``A1B2C3D4``.

    **Example:** Paragraph and revision elements get the same rsid for one logical edit burst.
    """
    return f"{secrets.randbelow(0xFFFFFFFF + 1):08X}"


def register_rsid(doc: Document, rsid: str) -> None:
    """Append ``rsid`` to ``<w:rsids>`` in settings if that value is not listed yet.

    **Why:** Word tracks which random ids appear in the document; omitting registration can cause
    validation quirks in strict tooling.

    **Args:**
        doc: The document whose ``settings.xml`` is updated.
        rsid: Value returned by ``new_rsid()``.
    """
    rsids_elm = doc.settings._element.find(qn("w:rsids"))
    if rsids_elm is None:
        return
    for child in rsids_elm.findall(qn("w:rsid")):
        if child.get(qn("w:val")) == rsid:
            return
    rsids_elm.append(OxmlElement("w:rsid", attrs={qn("w:val"): rsid}))


def runs_in_paragraph_doc_order(p_elm) -> list:
    """Collect ``<w:r>`` elements under a paragraph in reading order.

    **Algorithm:**

    1. Walk direct children of ``p_elm`` (the ``<w:p>`` element).
    2. If the child is ``<w:r>``, append it.
    3. If the child is ``<w:ins>`` or ``<w:del>``, append every nested ``<w:r>`` (track-change runs
       live inside the wrapper).

    **Returns:** List of ``CT_R`` (run) elements for anchoring comments from first to last run.

    **Example:** A paragraph ``<w:p><w:ins><w:r>…</w:r></w:ins></w:p>`` yields a single run object
    for comment range start/end placement.
    """
    out: list = []
    r_tag = qn("w:r")
    for child in p_elm:
        if child.tag == r_tag:
            out.append(child)
        elif child.tag in _INS_DEL:
            out.extend(child.findall(r_tag))
    return out


def _run_with_optional_color(hex6: str | None):
    """Build ``<w:r>`` with optional ``<w:color w:val="RRGGBB"/>``.

    **Args:**
        hex6: Six hex digits (e.g. ``C00000`` for red). ``None`` → no color property (use theme
        / default; good for accepted insertions that should stay black).

    **Returns:** An ``lxml`` element for ``w:r`` (run).

    **Example:** ``_run_with_optional_color("C00000")`` marks deleted run text red in Word.
    """
    r = OxmlElement("w:r")
    if hex6:
        r_pr = OxmlElement("w:rPr")
        r_pr.append(OxmlElement("w:color", attrs={qn("w:val"): hex6.upper()}))
        r.append(r_pr)
    return r


def append_tracked_replacement_paragraph(
    doc: Document,
    original: str,
    suggested: str,
    *,
    author: str,
    timestamp: str,
    del_id: int,
    ins_id: int,
    del_color_hex: str | None = None,
    ins_color_hex: str | None = None,
):
    """Append one paragraph containing a tracked **delete** + **insert** pair.

    **Parameters**

    - ``original`` / ``suggested``: Text shown as removed / added. Use ``""`` for an empty deletion
      (pure insertion pair) or ``\"\\u200b\"`` for a visible-only placeholder when needed.
    - ``del_id`` / ``ins_id``: Two distinct revision ids (typically ``n`` and ``n+1`` off a shared
      counter).
    - ``del_color_hex`` / ``ins_color_hex``: Optional run colors inside the del/ins wrappers.

    **Algorithm (maps to the code order)**

    1. Add an empty paragraph via python-docx and replace its body with our sequence.
    2. Generate one ``rsid``; stamp it on the paragraph and register it in settings.
    3. Build ``<w:del>`` with ``<w:delText>`` holding ``original`` (author, date, ids, rsids).
    4. Build ``<w:ins>`` with ``<w:t>`` holding ``suggested``.
    5. Append ``del`` then ``ins`` under the paragraph (Word expects both siblings in one ``w:p``).

    **Returns:** The paragraph element ``CT_P`` (``._element`` of the new paragraph).

    **Example**

    ``original="Fee: 5%"``, ``suggested="Fee: 8%"`` → one paragraph showing red strike + new text as
    a tracked replacement when ``del_color_hex`` is red and ``ins_color_hex`` is ``None``.
    """
    p_elm = doc.add_paragraph()._element
    p_elm.clear_content()

    rsid = new_rsid()
    register_rsid(doc, rsid)
    p_elm.set(qn("w:rsidR"), rsid)
    p_elm.set(qn("w:rsidDel"), rsid)
    p_elm.set(qn("w:rsidP"), rsid)

    del_elm = OxmlElement(
        "w:del",
        attrs={
            qn("w:id"): str(del_id),
            qn("w:author"): author,
            qn("w:date"): timestamp,
            qn("w:rsidR"): rsid,
            qn("w:rsidDel"): rsid,
        },
    )
    r_del = _run_with_optional_color(del_color_hex)
    del_text = OxmlElement("w:delText")
    del_text.text = original
    del_text.set(qn("xml:space"), "preserve")
    r_del.append(del_text)
    del_elm.append(r_del)

    ins_elm = OxmlElement(
        "w:ins",
        attrs={
            qn("w:id"): str(ins_id),
            qn("w:author"): author,
            qn("w:date"): timestamp,
            qn("w:rsidR"): rsid,
        },
    )
    r_ins = _run_with_optional_color(ins_color_hex)
    t = OxmlElement("w:t")
    t.text = suggested
    t.set(qn("xml:space"), "preserve")
    r_ins.append(t)
    ins_elm.append(r_ins)

    p_elm.append(del_elm)
    p_elm.append(ins_elm)
    return p_elm

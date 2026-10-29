#!/usr/bin/env python3
"""Deterministic generator for the F0005 synthetic GL declarations qualification corpus.

SYNTHETIC DEVELOPMENT DATA. Every company, person, address, policy number and form
number below is fictional. This corpus lives outside ``golden-corpus/`` and is not
part of the frozen holdout.

Independence: expected values are taken only from the layout specifications in this
file. Nothing here imports, runs or reads any conversion/extraction code.

Run (from the product repo root):

    neuron/.venv/bin/python neuron/fixtures/qualification/build_corpus.py

Outputs (all relative to this directory): documents/*.pdf, expectations/*.json,
corpus.yaml, CORPUS-HASHES.txt, README.md. Two runs produce byte-identical files.
"""

from __future__ import annotations

import hashlib
import io
import json
import random
import re
import shutil
from pathlib import Path

from reportlab import rl_config

rl_config.invariant = 1  # fixed /ID, no timestamps -> byte-identical output

import pypdfium2 as pdfium  # noqa: E402
from PIL import Image, ImageFilter  # noqa: E402
from reportlab.lib.utils import ImageReader  # noqa: E402
from reportlab.pdfbase.pdfmetrics import stringWidth  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

HERE = Path(__file__).resolve().parent
DOC_DIR = HERE / "documents"
EXP_DIR = HERE / "expectations"

PAGE_W, PAGE_H = 612.0, 792.0  # US Letter, points
SCAN_DPI = 200
REGION_DPI = 200
CORPUS_ID = "f0005-gl-qualification-v1"
LABEL = (
    "SYNTHETIC DEVELOPMENT DATA - F0005 qualification corpus of fictional US commercial "
    "general liability declarations. Not production data. Not part of golden-corpus/ "
    "and not part of the frozen holdout."
)

PROFILES = {
    "gl-limits-a": ["each_occurrence_limit", "general_aggregate_limit"],
    "gl-limits-b": ["named_insured", "policy_period_start", "policy_period_end"],
}
FIELDS = [f for fs in PROFILES.values() for f in fs]
TAGS = ["unique", "repeated", "table-borne", "split-across-regions", "absent"]

# Label substrings that must NOT be printed anywhere in a document where the field is absent.
ABSENT_FORBIDDEN = {
    "each_occurrence_limit": ["each occurrence"],
    "general_aggregate_limit": ["general aggregate"],
    "named_insured": ["named insured"],
    "policy_period_start": ["policy period", "effective"],
    "policy_period_end": ["policy period", "expiration", "expires"],
}

F_EO, F_GA, F_NI, F_PS, F_PE = FIELDS

# Distractor labels (never the target fields).
L_PROD = "Products-Completed Operations Aggregate Limit"
L_PAI = "Personal and Advertising Injury Limit"
L_DTRP = "Damage to Premises Rented to You Limit"
L_MED = "Medical Expense Limit"
L_EO = "Each Occurrence Limit"
L_GA = "General Aggregate Limit (Other Than Products-Completed Operations)"


# --------------------------------------------------------------------------- model


class Surface:
    """A drawable area (a page, or an image region on a page) that records ops."""

    def __init__(self, doc: "Doc", page_num: int, w: float, h: float, inset: float):
        self.doc, self.page_num, self.w, self.h, self.inset = doc, page_num, w, h, inset
        self.ops: list[tuple] = []

    def text(self, x, y, s, font="Helvetica", size=9.0, field=None, region=None,
             align="left", maxw=None):
        w = stringWidth(s, font, size)
        x0 = x - w if align == "right" else (x - w / 2 if align == "center" else x)
        assert x0 >= self.inset - 1e-6 and x0 + w <= self.w - self.inset + 1e-6, (
            self.doc.doc_id, self.page_num, s)
        assert 0 <= y <= self.h - size, (self.doc.doc_id, s, y)
        if maxw is not None:
            assert w <= maxw + 1e-6, (self.doc.doc_id, s, w, maxw)
        self.ops.append(("text", x0, y, s, font, size))
        self.doc.texts.append((self.page_num, s))
        if field is not None:
            assert region, "evidence needs a region name"
            self.doc.evidence[field].append({"page": self.page_num, "text": s, "region": region})
        return x0 + w

    def rect(self, x, y, w, h, fill=None, lw=0.6):
        self.ops.append(("rect", x, y, w, h, fill, lw))

    def line(self, x1, y1, x2, y2, lw=0.6):
        self.ops.append(("line", x1, y1, x2, y2, lw))


class Page(Surface):
    def __init__(self, doc, num):
        super().__init__(doc, num, PAGE_W, PAGE_H, inset=18)

    def image_region(self, x, y, w, h, name):
        """A rectangle whose content is embedded as pixels only (no text layer)."""
        r = Surface(self.doc, self.page_num, w, h, inset=2)
        r.name = name
        self.ops.append(("image", x, y, w, h, r))
        return r


class Doc:
    def __init__(self, doc_id, kind, layout, date_format, seed, damaged_pages=()):
        self.doc_id, self.kind, self.layout = doc_id, kind, layout
        self.date_format, self.seed = date_format, seed
        self.damaged_pages = list(damaged_pages)
        self.pages: list[Page] = []
        self.texts: list[tuple[int, str]] = []
        self.evidence = {f: [] for f in FIELDS}
        self.values = {f: None for f in FIELDS}
        self.tags: dict[str, list[str]] = {}
        self.notes = None

    def page(self) -> Page:
        p = Page(self, len(self.pages) + 1)
        self.pages.append(p)
        return p

    def expect(self, field, value, *tags):
        assert field in FIELDS and all(t in TAGS for t in tags), (field, tags)
        self.values[field] = value
        self.tags[field] = list(tags)

    # -- self-check of the spec (input data only) --------------------------------
    def validate(self):
        assert 1 <= len(self.pages) <= 3, self.doc_id
        for f in FIELDS:
            assert f in self.tags, (self.doc_id, f, "untagged")
            v, tags, ev = self.values[f], self.tags[f], self.evidence[f]
            ctx = (self.doc_id, f)
            assert not ("unique" in tags and "repeated" in tags), ctx
            if "absent" in tags:
                assert tags == ["absent"] and v is None and ev == [], ctx
                low = [s.lower() for _, s in self.texts]
                for bad in ABSENT_FORBIDDEN[f]:
                    assert not any(bad in s for s in low), (ctx, bad)
                continue
            assert v and ev, ctx
            assert all(e["page"] not in self.damaged_pages for e in ev), ctx
            if "split-across-regions" in tags:
                assert len(ev) == 2 and ev[0]["page"] == ev[1]["page"], ctx
                assert ev[0]["region"] != ev[1]["region"], ctx
                assert f"{ev[0]['text']} {ev[1]['text']}" == v, ctx
                assert not any(s == v for _, s in self.texts), ctx
            else:
                assert all(e["text"] == v for e in ev), ctx
                # every printed occurrence of the value is evidence (no stray copies)
                assert sum(1 for _, s in self.texts if s == v) == len(ev), ctx
                if "unique" in tags:
                    assert len(ev) == 1, ctx
            if "repeated" in tags:
                assert len(ev) >= 2, ctx
            if "table-borne" in tags:
                assert all("table" in e["region"] for e in ev), ctx

    def expectation_json(self):
        prof = {}
        for pname, fields in PROFILES.items():
            prof[pname] = {f: {"value": self.values[f], "evidence": self.evidence[f]}
                           for f in fields}
        out = {"document_id": self.doc_id, "kind": self.kind, "synthetic": True,
               "profiles": prof}
        if self.notes:
            out["notes"] = self.notes
        return out


# --------------------------------------------------------------------------- helpers


class C:
    """Table cell."""

    def __init__(self, s, field=None, region=None, align="left", bold=False):
        self.s, self.field, self.region, self.align, self.bold = s, field, region, align, bold


def table(pg, x, ytop, widths, rows, name, rh=16.0, size=8.5, header_rows=1,
          font="Helvetica", bold_font="Helvetica-Bold", pad=4.0, shade=0.88):
    total, n = sum(widths), len(rows)
    for i in range(header_rows):
        pg.rect(x, ytop - (i + 1) * rh, total, rh, fill=shade, lw=0)
    pg.rect(x, ytop - n * rh, total, n * rh)
    for i in range(1, n):
        pg.line(x, ytop - i * rh, x + total, ytop - i * rh, lw=0.4)
    cx = x
    for wcol in widths[:-1]:
        cx += wcol
        pg.line(cx, ytop, cx, ytop - n * rh, lw=0.4)
    for i, row in enumerate(rows):
        assert len(row) == len(widths), (name, row)
        cx = x
        for j, cell in enumerate(row):
            if cell is not None:
                if isinstance(cell, str):
                    cell = C(cell)
                f = bold_font if (i < header_rows or cell.bold) else font
                ty = ytop - (i + 1) * rh + (rh - size) / 2 + 1.2
                region = cell.region or f"{name}.r{i + 1}c{j + 1}"
                if cell.align == "right":
                    tx = cx + widths[j] - pad
                elif cell.align == "center":
                    tx = cx + widths[j] / 2
                else:
                    tx = cx + pad
                pg.text(tx, ty, cell.s, f, size, field=cell.field, region=region,
                        align=cell.align, maxw=widths[j] - 2 * pad)
            cx += widths[j]
    return ytop - n * rh


def kv(pg, x, y, label, value, lw, field=None, region=None, size=9.0,
       lfont="Helvetica-Bold", vfont="Helvetica", align="left", vx=None):
    pg.text(x, y, label, lfont, size)
    if align == "right":
        return pg.text(vx, y, value, vfont, size, field=field, region=region, align="right")
    return pg.text(x + lw, y, value, vfont, size, field=field, region=region)


def leader(pg, x, y, label, value, vx, field=None, region=None, size=9.0, font="Helvetica"):
    """'Label ........ value' line with the value right-aligned at vx."""
    end = pg.text(x, y, label, font, size)
    vw = stringWidth(value, font, size)
    dot_w = stringWidth(".", font, size)
    room = vx - vw - end - 8
    if room > dot_w * 3:
        pg.text(end + 4, y, "." * int(room / dot_w), font, size)
    pg.text(vx, y, value, font, size, field=field, region=region, align="right")


def header(pg, insurer, policy_no, form_no, page_of, title="COMMERCIAL GENERAL LIABILITY DECLARATIONS",
           font="Helvetica-Bold"):
    pg.text(54, 752, insurer, font, 12)
    pg.text(558, 752, f"Policy Number: {policy_no}", "Helvetica", 8.5, align="right")
    pg.line(54, 744, 558, 744, lw=1.2)
    pg.text(306, 726, title, font, 11, align="center")
    pg.text(54, 30, form_no, "Helvetica", 7)
    pg.text(558, 30, page_of, "Helvetica", 7, align="right")


def para(pg, x, y, lines, size=7.5, font="Helvetica", lead=10.0):
    for ln in lines:
        pg.text(x, y, ln, font, size)
        y -= lead
    return y


BOILER = [
    "These Declarations, together with the Common Policy Conditions, Coverage Form(s) and any",
    "Endorsement(s), complete the above numbered policy. Coverage is provided only for those",
    "coverages for which a limit or premium is shown.",
]


# --------------------------------------------------------------------------- documents


def doc_001():
    d = Doc("gl-q-001", "native", "label-value-lines", "MM/DD/YYYY", 1001)
    NI, EO, GA = "Copperline Fabrication Works LLC", "$1,000,000", "$2,000,000"
    PS, PE = "01/15/2026", "01/15/2027"
    d.expect(F_EO, EO, "unique"); d.expect(F_GA, GA, "unique")
    d.expect(F_NI, NI, "unique"); d.expect(F_PS, PS, "unique"); d.expect(F_PE, PE, "unique")
    p = d.page()
    header(p, "Harrowgate Mutual Casualty Company", "HMC-GL-4471-0001", "HMC GL DEC 01 26", "Page 1 of 1")
    y = 696
    kv(p, 54, y, "Named Insured:", NI, 110, F_NI, "insured-line")
    y -= 15; kv(p, 54, y, "Mailing Address:", "1450 Quarry Bend Road, Larkhaven, OH 43999", 110)
    y -= 15
    x = p.text(54, y, "Policy Period:", "Helvetica-Bold", 9)
    x = p.text(164, y, "From", "Helvetica", 9)
    x = p.text(x + 4, y, PS, "Helvetica", 9, field=F_PS, region="period-line")
    x = p.text(x + 4, y, "to", "Helvetica", 9)
    x = p.text(x + 4, y, PE, "Helvetica", 9, field=F_PE, region="period-line")
    p.text(x + 4, y, "at 12:01 A.M. standard time at your mailing address.", "Helvetica", 9)
    y -= 15; kv(p, 54, y, "Producer:", "Tallow Creek Insurance Agency, Larkhaven, OH", 110)
    y -= 15; kv(p, 54, y, "Date Issued:", "01/08/2026", 110)
    y -= 15; kv(p, 54, y, "Form of Business:", "Limited Liability Company", 110)
    y -= 28
    p.text(54, y, "LIMITS OF INSURANCE", "Helvetica-Bold", 10)
    y -= 18; leader(p, 54, y, L_EO, EO, 470, F_EO, "limits-lines")
    y -= 15; leader(p, 54, y, L_DTRP, "$100,000", 470); p.text(476, y, "Any one premises", "Helvetica", 7.5)
    y -= 15; leader(p, 54, y, L_MED, "$5,000", 470); p.text(476, y, "Any one person", "Helvetica", 7.5)
    y -= 15; leader(p, 54, y, L_PAI, "$500,000", 470); p.text(476, y, "Any one person", "Helvetica", 7.5)
    y -= 15; leader(p, 54, y, L_GA, GA, 470, F_GA, "limits-lines")
    y -= 15; leader(p, 54, y, L_PROD, "$3,000,000", 470)
    y -= 30
    p.text(54, y, "BUSINESS DESCRIPTION AND PREMIUM", "Helvetica-Bold", 10)
    y -= 16; kv(p, 54, y, "Business Description:", "Structural steel fabrication and welding", 130)
    y -= 15; kv(p, 54, y, "Advance Premium:", "$14,812", 130)
    y -= 15; kv(p, 54, y, "Minimum Premium:", "$2,500", 130)
    y -= 30
    para(p, 54, y, BOILER)
    return d


def doc_002():
    d = Doc("gl-q-002", "native", "header-box-and-limits-table", "Month D, YYYY", 1002)
    NI, EO, GA = "Halvorsen Brick & Stone Masonry, Inc.", "$2,000,000", "$4,000,000"
    PS, PE = "March 1, 2026", "March 1, 2027"
    d.expect(F_EO, EO, "table-borne", "unique"); d.expect(F_GA, GA, "table-borne", "unique")
    d.expect(F_NI, NI, "repeated"); d.expect(F_PS, PS, "repeated"); d.expect(F_PE, PE, "repeated")
    ins = "Northfen Indemnity Insurance Company"
    p = d.page()
    header(p, ins, "NFI-CGL-208815", "NFI CG DEC 03 26", "Page 1 of 2")
    p.rect(54, 610, 504, 100)
    p.text(62, 696, "Named Insured and Mailing Address", "Helvetica-Bold", 8)
    p.text(62, 682, NI, "Helvetica", 10, field=F_NI, region="header-box.insured")
    p.text(62, 668, "88 Kilnworth Avenue", "Helvetica", 9)
    p.text(62, 656, "Brindlemoor, PA 19999", "Helvetica", 9)
    p.line(330, 710, 330, 610)
    p.text(338, 696, "Policy Period", "Helvetica-Bold", 8)
    x = p.text(338, 682, PS, "Helvetica", 9, field=F_PS, region="header-box.period")
    x = p.text(x + 4, 682, "to", "Helvetica", 9)
    p.text(x + 4, 682, PE, "Helvetica", 9, field=F_PE, region="header-box.period")
    p.text(338, 670, "12:01 A.M. standard time", "Helvetica", 8)
    p.text(338, 650, "Producer", "Helvetica-Bold", 8)
    p.text(338, 638, "Saltmarsh Risk Partners", "Helvetica", 9)
    p.text(338, 622, "Issued: February 20, 2026", "Helvetica", 8)
    p.text(54, 588, "LIMITS OF INSURANCE", "Helvetica-Bold", 10)
    rows = [
        ["Coverage", "Limit", "Basis"],
        [L_EO, C(EO, F_EO, align="right"), "Any one occurrence"],
        [L_GA, C(GA, F_GA, align="right"), "Policy period"],
        [L_PROD, C("$3,000,000", align="right"), "Policy period"],
        [L_PAI, C("$1,000,000", align="right"), "Any one person or organization"],
        [L_DTRP, C("$300,000", align="right"), "Any one premises"],
        [L_MED, C("$10,000", align="right"), "Any one person"],
    ]
    y = table(p, 54, 580, [290, 80, 134], rows, "limits-table", size=8)
    y -= 26
    p.text(54, y, "RETROACTIVE DATE: None", "Helvetica", 8.5)
    y -= 24
    para(p, 54, y, BOILER)
    p2 = d.page()
    header(p2, ins, "NFI-CGL-208815", "NFI CG DEC 03 26", "Page 2 of 2",
           title="SCHEDULE OF CLASSIFICATIONS AND PREMIUM")
    kv(p2, 54, 700, "Named Insured:", NI, 86, F_NI, "page2-header.insured", size=8.5)
    p2.text(54, 686, "Policy Period:", "Helvetica-Bold", 8.5)
    x = p2.text(140, 686, PS, "Helvetica", 8.5, field=F_PS, region="page2-header.period")
    x = p2.text(x + 4, 686, "to", "Helvetica", 8.5)
    p2.text(x + 4, 686, PE, "Helvetica", 8.5, field=F_PE, region="page2-header.period")
    rows = [
        ["Class Code", "Classification", "Premium Base", "Rate", "Premium"],
        ["98449", "Masonry - commercial", "Payroll $612,400", "11.204", C("$6,861", align="right")],
        ["98483", "Stone work - interior", "Payroll $148,000", "9.872", C("$1,461", align="right")],
        ["91580", "Contractors - executive supervisors", "Payroll $95,000", "4.115", C("$391", align="right")],
    ]
    y = table(p2, 54, 664, [66, 170, 110, 60, 98], rows, "class-table", size=8)
    y -= 20
    kv(p2, 54, y, "Total Advance Premium:", "$8,713", 130, size=9)
    return d


def doc_003():
    d = Doc("gl-q-003", "native", "two-column", "YYYY-MM-DD", 1003)
    NI1, NI2 = "Bluegate Orchard and Cold Storage", "Cooperative Association, Inc."
    EO, PS, PE = "$1,000,000", "2026-04-01", "2027-04-01"
    d.expect(F_EO, EO, "repeated"); d.expect(F_GA, None, "absent")
    d.expect(F_NI, f"{NI1} {NI2}", "split-across-regions")
    d.expect(F_PS, PS, "table-borne", "unique"); d.expect(F_PE, PE, "table-borne", "unique")
    ins = "Quillfeather Casualty Exchange"
    p = d.page()
    header(p, ins, "QCE-GL-0003921", "QCE-GLD 2026-01", "Page 1 of 2")
    # left column
    p.rect(54, 610, 240, 100)
    p.text(62, 696, "NAMED INSURED", "Helvetica-Bold", 8)
    p.text(62, 682, NI1, "Helvetica", 9.5, field=F_NI, region="insured-box.line1")
    p.text(62, 669, NI2, "Helvetica", 9.5, field=F_NI, region="insured-box.line2")
    p.text(62, 652, "4021 Pippin Hollow Lane", "Helvetica", 9)
    p.text(62, 640, "Marrowdale, WA 98999", "Helvetica", 9)
    # right column
    p.text(318, 700, "TERM", "Helvetica-Bold", 8)
    table(p, 318, 694, [120, 120], [["Effective", "Expiration"],
                                    [C(PS, F_PS), C(PE, F_PE)]], "period-table", rh=18, size=9)
    p.text(318, 640, "Issue Date: 2026-03-25", "Helvetica", 8.5)
    p.text(318, 626, "Agent: Fernleigh & Osgood Brokerage", "Helvetica", 8.5)
    p.text(54, 584, "LIMITS OF INSURANCE", "Helvetica-Bold", 10)
    y = 566
    left = [("Each Occurrence", EO, F_EO, "limits-col-left"), ("Damage to Rented Premises", "$50,000", None, None),
            ("Medical Expense (Any One Person)", "$5,000", None, None)]
    right = [("Personal & Advertising Injury", "$750,000"), ("Products-Completed Operations Aggregate", "$2,000,000")]
    for lbl, val, fld, reg in left:
        p.text(54, y, lbl, "Helvetica", 9)
        p.text(290, y, val, "Helvetica-Bold", 9, field=fld, region=reg, align="right")
        y -= 15
    y = 566
    for lbl, val in right:
        p.text(318, y, lbl, "Helvetica", 9)
        p.text(558, y, val, "Helvetica-Bold", 9, align="right")
        y -= 15
    y = 500
    p.text(54, y, "DESCRIPTION OF OPERATIONS", "Helvetica-Bold", 10)
    para(p, 54, y - 16, ["Fruit orchard operation with cold storage warehouse; seasonal packing line.",
                         "Location 1: 4021 Pippin Hollow Lane, Marrowdale, WA 98999"], size=8.5, lead=12)
    para(p, 54, y - 60, BOILER)
    p2 = d.page()
    header(p2, ins, "QCE-GL-0003921", "QCE-GLD 2026-01", "Page 2 of 2",
           title="ADDITIONAL INSURED - VENDORS SCHEDULE")
    p2.text(54, 700, "Name of Additional Insured Person(s) or Organization(s):", "Helvetica-Bold", 9)
    p2.text(54, 686, "Gristmill Lane Grocers Cooperative", "Helvetica", 9)
    p2.text(54, 666, "Limits applicable to the additional insured under this endorsement:", "Helvetica-Bold", 9)
    x = p2.text(54, 652, "Each Occurrence:", "Helvetica", 9)
    p2.text(x + 6, 652, EO, "Helvetica", 9, field=F_EO, region="endorsement-limits-line")
    p2.text(54, 638, "Products-Completed Operations: included", "Helvetica", 9)
    para(p2, 54, 610, ["Coverage for the additional insured is limited to bodily injury or property damage arising",
                       "out of products distributed or sold in the regular course of the vendor's business."])
    return d


def doc_004():
    d = Doc("gl-q-004", "native", "dollar-sign-column-table", "Month D, YYYY (wrapped)", 1004)
    NI = "Tamarind Street Bakery Group LLC"
    d.expect(F_EO, "$ 500,000", "table-borne", "split-across-regions")
    d.expect(F_GA, "$ 1,000,000", "table-borne", "split-across-regions")
    d.expect(F_NI, NI, "unique")
    d.expect(F_PS, "June 30, 2026", "split-across-regions")
    d.expect(F_PE, "June 30, 2027", "split-across-regions")
    ins = "Corrigan Bay Assurance Company"
    p = d.page()
    header(p, ins, "CBA 77-310-4459", "CBA-CGL-DEC (06-26)", "Page 1 of 1")
    p.text(54, 702, "Item 1.", "Helvetica-Bold", 9)
    kv(p, 100, 702, "Named Insured:", NI, 84, F_NI, "item1-line")
    p.text(100, 688, "312 Tamarind Street, Oxbury Falls, GA 30999", "Helvetica", 9)
    p.text(54, 666, "Item 2.", "Helvetica-Bold", 9)
    p.text(100, 666, "Policy Period", "Helvetica-Bold", 9)
    # narrow boxes: each date wraps onto a second line
    for i, (lbl, yr, fld) in enumerate([("From:", "2026", F_PS), ("To:", "2027", F_PE)]):
        bx = 100 + i * 96
        p.rect(bx, 618, 88, 40)
        p.text(bx + 4, 646, lbl, "Helvetica-Bold", 8)
        p.text(bx + 30, 646, "June 30,", "Helvetica", 9, field=fld, region=f"period-{lbl[:-1].lower()}-box.line1")
        p.text(bx + 30, 634, yr, "Helvetica", 9, field=fld, region=f"period-{lbl[:-1].lower()}-box.line2")
        p.text(bx + 4, 622, "12:01 A.M.", "Helvetica", 6.5)
    p.text(310, 646, "Date of Issue: 06/18/2026", "Helvetica", 8.5)
    p.text(310, 632, "Producer: Larchmont Pike Agency Inc.", "Helvetica", 8.5)
    p.text(54, 596, "Item 3.", "Helvetica-Bold", 9)
    p.text(100, 596, "Limits of Insurance", "Helvetica-Bold", 9)

    def amt(v, field=None, rname=None):
        return [C("$", field, f"limits-table.{rname}.currency" if rname else None, align="center"),
                C(v, field, f"limits-table.{rname}.amount" if rname else None, align="right")]

    rows = [["Coverage", "", "Amount"],
            [L_EO, *amt("500,000", F_EO, "each-occurrence")],
            [L_GA, *amt("1,000,000", F_GA, "general-aggregate")],
            [L_PROD, *amt("2,000,000")],
            [L_PAI, *amt("250,000")],
            ["Damage to Premises Rented to You (Any One Premises)", *amt("100,000")],
            ["Medical Expense (Any One Person)", *amt("5,000")]]
    y = table(p, 100, 588, [300, 22, 80], rows, "limits-table", size=8)
    y -= 24
    p.text(54, y, "Item 4.", "Helvetica-Bold", 9)
    kv(p, 100, y, "Premium:", "Advance premium $3,975, subject to audit", 50)
    y -= 26
    para(p, 54, y, BOILER)
    return d


def doc_005():
    d = Doc("gl-q-005", "native", "supplemental-declarations", "MM/DD/YYYY", 1005)
    NI, GA, PS = "Kestrel Point Marine Supply Co.", "$3,000,000", "07/01/2026"
    d.expect(F_EO, None, "absent"); d.expect(F_GA, GA, "unique")
    d.expect(F_NI, NI, "repeated"); d.expect(F_PS, PS, "unique"); d.expect(F_PE, None, "absent")
    d.notes = ("Each Occurrence Limit and policy expiration are deliberately not printed "
               "(continuous-term supplemental declarations); traps: Products-Completed Operations "
               "Aggregate and other limits, issue date.")
    ins = "Bramblewick General Insurance Corp."
    p = d.page()
    header(p, ins, "BGI-SD-55102", "BGI GL SUPP 07 26", "Page 1 of 1",
           title="COMMERCIAL GENERAL LIABILITY SUPPLEMENTAL DECLARATIONS")
    kv(p, 54, 700, "Named Insured:", NI, 96, F_NI, "insured-line")
    kv(p, 54, 686, "Address:", "17 Breakwater Row, Gullhaven, ME 04999", 96)
    kv(p, 54, 672, "Effective Date:", PS, 96, F_PS, "effective-line")
    kv(p, 54, 658, "Policy Term:", "Continuous until cancelled", 96)
    kv(p, 54, 644, "Date Issued:", "06/24/2026", 96)
    p.text(54, 616, "AGGREGATE AND OTHER LIMITS", "Helvetica-Bold", 10)
    y = 598
    for lbl, val, fld in [("General Aggregate Limit (Other Than Products-Completed Operations):", GA, F_GA),
                          (L_PROD + ":", "$2,000,000", None),
                          (L_PAI + ":", "$1,000,000", None),
                          (L_DTRP + ":", "$100,000", None),
                          (L_MED + ":", "$5,000", None)]:
        p.text(54, y, lbl, "Helvetica", 9)
        p.text(558, y, val, "Helvetica", 9, field=fld, region="aggregate-lines" if fld else None, align="right")
        y -= 15
    y -= 20
    para(p, 54, y, ["This Supplemental Declarations page amends the limits shown above only. All other",
                    "terms and conditions of the policy remain unchanged."], size=8)
    y -= 70
    p.line(330, y + 12, 558, y + 12)
    p.text(330, y, "Authorized Representative", "Helvetica", 7.5)
    y -= 20
    kv(p, 330, y, "Issued to:", NI, 50, F_NI, "countersignature-block", size=8)
    return d


def doc_006():
    d = Doc("gl-q-006", "native", "insured-schedule-table-plus-recap", "YYYY-MM-DD", 1006)
    NI, EO, GA, PS, PE = "Ridgeback Survey & Mapping Co.", "$1,000,000", "$2,000,000", "2026-09-15", "2027-09-15"
    d.expect(F_EO, EO, "table-borne", "repeated"); d.expect(F_GA, GA, "table-borne", "repeated")
    d.expect(F_NI, NI, "table-borne", "unique"); d.expect(F_PS, PS, "unique"); d.expect(F_PE, PE, "unique")
    ins = "Tessaract Mutual Fire & Casualty"
    p = d.page()
    header(p, ins, "TMFC/GL/060615", "TMFC-GL-01 (2026)", "Page 1 of 2")
    table(p, 54, 708, [140, 364], [
        ["Item", "Particulars"],
        ["Named Insured", C(NI, F_NI, "insured-table.r2c2")],
        ["Form of Business", "Corporation"],
        ["Mailing Address", "906 Theodolite Way, Cairnbrook, CO 80999"],
        ["Producer", "Ashgrove Underwriting Services"],
    ], "insured-table", rh=17)
    y = 610
    x = p.text(54, y, "Policy Period:", "Helvetica-Bold", 9)
    x = p.text(x + 6, y, PS, "Helvetica", 9, field=F_PS, region="period-line")
    x = p.text(x + 4, y, "to", "Helvetica", 9)
    x = p.text(x + 4, y, PE, "Helvetica", 9, field=F_PE, region="period-line")
    p.text(x + 4, y, "(12:01 A.M. local time)", "Helvetica", 8)
    p.text(54, 594, "Retroactive Date: 2019-09-15", "Helvetica", 8.5)
    p.text(54, 566, "LIMITS OF INSURANCE", "Helvetica-Bold", 10)
    rows = [["Limit", "Amount"],
            [L_GA, C(GA, F_GA, align="right")],
            [L_PROD, C("$1,500,000", align="right")],
            [L_PAI, C("$600,000", align="right")],
            [L_EO, C(EO, F_EO, align="right")],
            [L_DTRP, C("$300,000", align="right")],
            [L_MED, C("$15,000", align="right")]]
    y = table(p, 54, 558, [384, 120], rows, "limits-table", size=8.5)
    para(p, 54, y - 24, BOILER)
    p2 = d.page()
    header(p2, ins, "TMFC/GL/060615", "TMFC-GL-01 (2026)", "Page 2 of 2", title="LIMITS RECAP AND PREMIUM")
    rows = [["Coverage Part", "Limit", "Premium"],
            ["Each Occurrence", C(EO, F_EO, align="right"), C("$5,120", align="right")],
            ["General Aggregate", C(GA, F_GA, align="right"), C("included", align="right")],
            ["Products-Completed Operations Aggregate", C("$1,500,000", align="right"), C("$1,388", align="right")],
            ["Terrorism (TRIA)", C("included", align="right"), C("$65", align="right")]]
    y = table(p2, 54, 700, [264, 120, 120], rows, "recap-table", size=8.5)
    kv(p2, 54, y - 20, "Total Policy Premium:", "$6,573", 120)
    return d


def doc_007():
    d = Doc("gl-q-007", "scanned", "label-value-lines-scanned", "Month D, YYYY", 1007)
    NI1, NI2 = "Wexford Line Hydraulic Repair", "and Fleet Services, LLC"
    EO, GA, PS, PE = "$1,000,000", "$2,000,000", "February 10, 2026", "February 10, 2027"
    d.expect(F_EO, EO, "unique"); d.expect(F_GA, GA, "unique")
    d.expect(F_NI, f"{NI1} {NI2}", "split-across-regions")
    d.expect(F_PS, PS, "repeated"); d.expect(F_PE, PE, "repeated")
    ins = "Pemberton Glen Insurance Company"
    p = d.page()
    header(p, ins, "PGI-CGL-117-2026", "PGI DEC GL 02 26", "Page 1 of 2", font="Times-Bold")
    F = "Times-Roman"
    p.text(54, 700, "Named Insured:", "Times-Bold", 11)
    p.text(160, 700, NI1, F, 11, field=F_NI, region="insured-line1")
    p.text(160, 686, NI2, F, 11, field=F_NI, region="insured-line2")
    kv(p, 54, 668, "Address:", "2290 Gantry Road, Ellisport, MI 48999", 106, size=11, lfont="Times-Bold", vfont=F)
    p.text(54, 650, "Policy Period:", "Times-Bold", 11)
    x = p.text(160, 650, PS, F, 11, field=F_PS, region="period-line")
    x = p.text(x + 4, 650, "to", F, 11)
    p.text(x + 4, 650, PE, F, 11, field=F_PE, region="period-line")
    kv(p, 54, 632, "Producer:", "Halloway & Crisp Insurance Brokers", 106, size=11, lfont="Times-Bold", vfont=F)
    kv(p, 54, 614, "Issued:", "January 30, 2026", 106, size=11, lfont="Times-Bold", vfont=F)
    p.text(54, 584, "LIMITS OF INSURANCE", "Times-Bold", 12)
    y = 564
    for lbl, val, fld in [(L_EO, EO, F_EO), (L_GA, GA, F_GA), (L_PROD, "$2,500,000", None),
                          (L_PAI, "$500,000", None), (L_DTRP, "$100,000", None), (L_MED, "$5,000", None)]:
        leader(p, 54, y, lbl, val, 520, fld, "limits-lines" if fld else None, size=10.5, font=F)
        y -= 17
    para(p, 54, y - 20, BOILER, size=9, font=F, lead=12)
    p2 = d.page()
    header(p2, ins, "PGI-CGL-117-2026", "PGI DEC GL 02 26", "Page 2 of 2", font="Times-Bold",
           title="SCHEDULE OF HAZARDS")
    x = p2.text(54, 700, "Policy Period:", "Times-Bold", 10.5)
    x = p2.text(x + 6, 700, PS, F, 10.5, field=F_PS, region="page2-period-line")
    x = p2.text(x + 4, 700, "-", F, 10.5)
    p2.text(x + 4, 700, PE, F, 10.5, field=F_PE, region="page2-period-line")
    rows = [["Loc.", "Classification", "Code", "Exposure", "Premium"],
            ["1", "Machinery repair - hydraulic", "97003", "Gross sales $1,840,000", C("$4,232", align="right")],
            ["1", "Auto repair - fleet service", "10073", "Gross sales $910,000", C("$2,184", align="right")]]
    table(p2, 54, 678, [36, 190, 54, 130, 94], rows, "hazard-table", rh=18, size=9.5,
          font=F, bold_font="Times-Bold")
    return d


def doc_008():
    d = Doc("gl-q-008", "scanned", "tables-scanned", "MM/DD/YYYY", 1008)
    NI, EO, GA, PS, PE = "Oriel Valley Greenhouse Partners, L.P.", "$500,000", "$1,000,000", "05/20/2026", "05/20/2027"
    d.expect(F_EO, EO, "table-borne", "unique"); d.expect(F_GA, GA, "table-borne", "repeated")
    d.expect(F_NI, NI, "unique"); d.expect(F_PS, PS, "table-borne", "unique"); d.expect(F_PE, PE, "table-borne", "unique")
    ins = "Lanternhill Specialty Insurance Co."
    p = d.page()
    header(p, ins, "LSI-GL-00842-08", "LSI-GL-DEC-0526", "Page 1 of 2")
    kv(p, 54, 700, "NAMED INSURED:", NI, 100, F_NI, "insured-line", size=10)
    p.text(154, 686, "70 Trellis Bend, Saffron Ridge, CA 95999", "Helvetica", 9.5)
    table(p, 54, 664, [168, 168, 168], [["Policy Inception", "Policy Expiration", "Date Issued"],
                                        [C(PS, F_PS), C(PE, F_PE), "05/13/2026"]],
          "period-table", rh=20, size=9.5)
    p.text(54, 608, "LIMITS OF INSURANCE", "Helvetica-Bold", 11)
    rows = [["Coverage", "Limit"],
            ["Each Occurrence", C(EO, F_EO, align="right")],
            ["General Aggregate (other than Products-Completed Operations)", C(GA, F_GA, align="right")],
            ["Products-Completed Operations Aggregate", C("$1,500,000", align="right")],
            ["Personal & Advertising Injury", C("$250,000", align="right")],
            ["Damage to Rented Premises (any one premises)", C("$50,000", align="right")],
            ["Medical Expense (any one person)", C("$2,500", align="right")]]
    y = table(p, 54, 600, [380, 124], rows, "limits-table", rh=19, size=9.5)
    para(p, 54, y - 24, BOILER, size=8.5, lead=11)
    p2 = d.page()
    header(p2, ins, "LSI-GL-00842-08", "LSI-GL-DEC-0526", "Page 2 of 2", title="PREMIUM SUMMARY")
    rows = [["Item", "Limit / Basis", "Premium"],
            ["General Aggregate Limit", C(GA, F_GA, align="right"), C("$3,410", align="right")],
            ["Products-Completed Operations", C("$1,500,000", align="right"), C("$612", align="right")],
            ["Policy Fee", C("-", align="right"), C("$150", align="right")],
            [C("Total", bold=True), None, C("$4,172", align="right", bold=True)]]
    table(p2, 54, 700, [250, 130, 124], rows, "premium-table", rh=20, size=9.5)
    return d


def doc_009():
    d = Doc("gl-q-009", "scanned", "continuation-declarations-scanned", "YYYY-MM-DD", 1009)
    EO, GA, PS, PE = "$2,000,000", "$4,000,000", "2026-08-01", "2027-08-01"
    d.expect(F_EO, EO, "repeated"); d.expect(F_GA, GA, "unique")
    d.expect(F_NI, None, "absent"); d.expect(F_PS, PS, "unique"); d.expect(F_PE, PE, "unique")
    d.notes = ("Named Insured is deliberately not printed on this continuation declarations; traps: "
               "additional insured, certificate holder, insurer and producer names.")
    ins = "Galloway Fenn Insurance Company"
    p = d.page()
    header(p, ins, "GFI 4400918-09", "GFI CGL DEC CONT 08 26", "Page 1 of 1",
           title="COMMERCIAL GENERAL LIABILITY DECLARATIONS - CONTINUATION")
    x = p.text(54, 700, "Coverage Term:", "Helvetica-Bold", 10)
    x = p.text(x + 6, 700, PS, "Helvetica", 10, field=F_PS, region="term-line")
    x = p.text(x + 4, 700, "through", "Helvetica", 10)
    p.text(x + 4, 700, PE, "Helvetica", 10, field=F_PE, region="term-line")
    kv(p, 54, 684, "Producer:", "Wendover Isle Brokerage LLC", 110, size=10)
    kv(p, 54, 668, "Additional Insured:", "Fenwick Pier Holdings, Inc.", 110, size=10)
    kv(p, 54, 652, "Certificate Holder:", "Quayside Commons Owners Association", 110, size=10)
    kv(p, 54, 636, "Issued:", "2026-07-22", 110, size=10)
    p.text(54, 606, "LIMITS", "Helvetica-Bold", 11)
    y = 588
    for lbl, val, fld in [(L_EO, EO, F_EO), (L_GA, GA, F_GA), (L_PROD, "$3,000,000", None),
                          (L_PAI, "$1,000,000", None), (L_DTRP, "$500,000", None), (L_MED, "$10,000", None)]:
        kv(p, 54, y, lbl, val, 340, fld, "limits-lines" if fld else None, size=10, lfont="Helvetica")
        y -= 16
    y -= 16
    p.text(54, y, "COVERAGE SUMMARY", "Helvetica-Bold", 11)
    y -= 18
    x = p.text(54, y, "Bodily injury and property damage liability, each occurrence up to", "Helvetica", 9.5)
    p.text(x + 4, y, EO, "Helvetica", 9.5, field=F_EO, region="coverage-summary")
    para(p, 54, y - 30, BOILER, size=8.5, lead=11)
    return d


def doc_010():
    d = Doc("gl-q-010", "scanned", "insured-tables-wrapped-dates-scanned", "Month D, YYYY (wrapped)", 1010)
    NI, EO = "Sablewood Timber Framing Company", "$1,000,000"
    d.expect(F_EO, EO, "unique"); d.expect(F_GA, None, "absent")
    d.expect(F_NI, NI, "table-borne", "repeated")
    d.expect(F_PS, "October 5, 2026", "split-across-regions")
    d.expect(F_PE, "October 5, 2027", "split-across-regions")
    d.notes = "General Aggregate Limit deliberately not printed; trap: Products-Completed Operations Aggregate $2,000,000."
    ins = "Ironvale Reciprocal Insurance Exchange"
    p = d.page()
    header(p, ins, "IRIE-GL-31070", "IRIE GL D 10 26", "Page 1 of 2")
    table(p, 54, 708, [130, 374], [["Insured Information", ""],
                                   ["Named Insured", C(NI, F_NI, "insured-table.r2c2")],
                                   ["Address", "5 Mortise Lane, Pinecrest Hollow, VT 05999"]],
          "insured-table", rh=19, size=9.5)
    p.text(54, 632, "Policy Period", "Helvetica-Bold", 10)
    for i, (lbl, yr, fld, key) in enumerate([("Begins", "2026", F_PS, "begins"), ("Ends", "2027", F_PE, "ends")]):
        bx = 54 + i * 110
        p.rect(bx, 576, 100, 48)
        p.text(bx + 5, 610, lbl, "Helvetica-Bold", 8.5)
        p.text(bx + 5, 596, "October 5,", "Helvetica", 10, field=fld, region=f"period-{key}-box.line1")
        p.text(bx + 5, 583, yr, "Helvetica", 10, field=fld, region=f"period-{key}-box.line2")
    p.text(290, 610, "Issued: September 28, 2026", "Helvetica", 9)
    p.text(290, 596, "Producer: Hartsell Commons Agency", "Helvetica", 9)
    p.text(54, 548, "LIMITS OF INSURANCE", "Helvetica-Bold", 11)
    y = 530
    for lbl, val, fld in [(L_EO, EO, F_EO), (L_PROD, "$2,000,000", None), (L_PAI, "$500,000", None),
                          (L_DTRP, "$100,000", None), (L_MED, "$5,000", None)]:
        leader(p, 54, y, lbl, val, 470, fld, "limits-lines" if fld else None, size=10)
        y -= 16
    para(p, 54, y - 20, BOILER, size=8.5, lead=11)
    p2 = d.page()
    header(p2, ins, "IRIE-GL-31070", "IRIE GL D 10 26", "Page 2 of 2", title="FORMS AND ENDORSEMENTS")
    table(p2, 54, 708, [130, 374], [["Named Insured", C(NI, F_NI, "page2-header-table.r1c2")]],
          "page2-header-table", rh=19, size=9.5, header_rows=0)
    rows = [["Form Number", "Edition", "Title"],
            ["IRIE CG 00 01", "04 13", "Commercial General Liability Coverage Form"],
            ["IRIE CG 21 47", "12 07", "Employment-Related Practices Exclusion"],
            ["IRIE IL 00 17", "11 98", "Common Policy Conditions"]]
    table(p2, 54, 670, [110, 60, 334], rows, "forms-table", rh=19, size=9.5)
    return d


def doc_011():
    d = Doc("gl-q-011", "mixed", "image-header-native-limits", "MM/DD/YYYY", 1011)
    NI, EO, GA, PS, PE = ("Ashcombe Ridge Veterinary Associates, PLLC", "$1,000,000", "$3,000,000",
                          "11/01/2026", "11/01/2027")
    d.expect(F_EO, EO, "table-borne", "unique"); d.expect(F_GA, GA, "repeated")
    d.expect(F_NI, NI, "unique"); d.expect(F_PS, PS, "unique"); d.expect(F_PE, PE, "unique")
    d.notes = ("Named insured, policy period and one General Aggregate occurrence are printed only inside "
               "the pixel-only image region 'header-image'; the limits table has a text layer.")
    ins = "Selkirk Moor Casualty Company"
    p = d.page()
    header(p, ins, "SMC-GL-91177", "SMC GL DEC 11 26", "Page 1 of 1")
    r = p.image_region(54, 600, 504, 112, "header-image")
    r.rect(1, 1, 502, 110, lw=1.0)
    r.text(10, 94, "NAMED INSURED", "Helvetica-Bold", 8)
    r.text(10, 80, NI, "Helvetica", 10, field=F_NI, region="header-image.insured")
    r.text(10, 66, "1188 Whitlow Pasture Road, Dunmere, KY 40999", "Helvetica", 9)
    r.text(10, 46, "POLICY PERIOD", "Helvetica-Bold", 8)
    x = r.text(10, 32, PS, "Helvetica", 10, field=F_PS, region="header-image.period")
    x = r.text(x + 4, 32, "to", "Helvetica", 10)
    r.text(x + 4, 32, PE, "Helvetica", 10, field=F_PE, region="header-image.period")
    r.text(330, 94, "AGGREGATE AT A GLANCE", "Helvetica-Bold", 8)
    x = r.text(330, 80, "General Aggregate:", "Helvetica", 9)
    r.text(x + 4, 80, GA, "Helvetica", 9, field=F_GA, region="header-image.aggregate")
    r.text(330, 46, "ISSUED", "Helvetica-Bold", 8)
    r.text(330, 32, "10/24/2026", "Helvetica", 10)
    p.text(54, 578, "LIMITS OF INSURANCE", "Helvetica-Bold", 10)
    rows = [["Coverage", "Limit"],
            [L_EO, C(EO, F_EO, align="right")],
            [L_GA, C(GA, F_GA, "limits-table.r3c2", align="right")],
            [L_PROD, C("$2,000,000", align="right")],
            [L_PAI, C("$500,000", align="right")],
            [L_DTRP, C("$100,000", align="right")],
            [L_MED, C("$5,000", align="right")]]
    y = table(p, 54, 570, [384, 120], rows, "limits-table", size=8.5)
    kv(p, 54, y - 24, "Producer:", "Brackenridge & Vale Insurance Services", 60, size=9)
    para(p, 54, y - 50, BOILER)
    return d


def doc_012():
    d = Doc("gl-q-012", "mixed", "native-header-image-limits-table", "n/a (period absent)", 1012)
    NI, EO, GA = "Pellucid Glassworks Studio, Inc.", "$1,000,000", "$2,000,000"
    d.expect(F_EO, EO, "table-borne", "unique"); d.expect(F_GA, GA, "table-borne", "unique")
    d.expect(F_NI, NI, "unique"); d.expect(F_PS, None, "absent"); d.expect(F_PE, None, "absent")
    d.notes = ("Policy period start and end are deliberately not printed; traps: issue date and retroactive "
               "date. The limits table is a pixel-only image region 'limits-table-image'.")
    ins = "Thornbury Lane Insurance Company"
    p = d.page()
    header(p, ins, "TLI-CGL-120412", "TLI CG DEC 02 26", "Page 1 of 1")
    kv(p, 54, 700, "Named Insured:", NI, 100, F_NI, "insured-line", size=10)
    kv(p, 54, 685, "Mailing Address:", "640 Annealing Court, Fairlight Bay, OR 97999", 100, size=10)
    kv(p, 54, 670, "Date Issued:", "2026-02-02", 100, size=10)
    kv(p, 54, 655, "Retroactive Date:", "2021-02-01", 100, size=10)
    p.text(54, 626, "LIMITS OF INSURANCE (schedule reproduced from rating worksheet)", "Helvetica-Bold", 10)
    r = p.image_region(54, 470, 504, 146, "limits-table-image")
    rows = [["Coverage", "Limit"],
            [L_EO, C(EO, F_EO, "limits-table-image.r2c2", align="right")],
            [L_GA, C(GA, F_GA, "limits-table-image.r3c2", align="right")],
            [L_PROD, C("$3,000,000", align="right")],
            [L_PAI, C("$500,000", align="right")],
            [L_DTRP, C("$100,000", align="right")],
            [L_MED, C("$5,000", align="right")]]
    table(r, 4, 142, [376, 120], rows, "limits-table-image", rh=19, size=9)
    kv(p, 54, 446, "Producer:", "Cindermill Insurance Advisors", 60, size=9)
    para(p, 54, 420, BOILER)
    return d


def doc_013():
    d = Doc("gl-q-013", "partial", "three-page-with-damaged-page", "Month D, YYYY", 1013, damaged_pages=[2])
    NI, EO, GA = "Marlowe Junction Freight Terminal, Inc.", "$1,000,000", "$2,000,000"
    PS, PE = "December 15, 2025", "December 15, 2026"
    d.expect(F_EO, EO, "unique"); d.expect(F_GA, GA, "unique")
    d.expect(F_NI, NI, "unique"); d.expect(F_PS, PS, "unique"); d.expect(F_PE, PE, "unique")
    d.notes = ("Page 2 (forms schedule) has a deliberately corrupted content stream and carries no expected "
               "values; every expected value is readable on intact pages 1 and 3.")
    ins = "Oakhurst Carrow Mutual Insurance Company"
    p = d.page()
    header(p, ins, "OCM-GL-131225", "OCM GL DEC 12 25", "Page 1 of 3")
    kv(p, 54, 700, "Named Insured:", NI, 96, F_NI, "insured-line")
    kv(p, 54, 686, "Address:", "3 Railspur Yard Road, Calder Flats, NE 68999", 96)
    kv(p, 54, 672, "Producer:", "Gilchrist Ferry Agency", 96)
    p.text(54, 644, "LIMITS OF INSURANCE", "Helvetica-Bold", 10)
    y = 626
    for lbl, val, fld in [(L_EO, EO, F_EO), (L_GA, GA, F_GA), (L_PROD, "$2,500,000", None),
                          (L_PAI, "$750,000", None), (L_DTRP, "$100,000", None), (L_MED, "$5,000", None)]:
        leader(p, 54, y, lbl, val, 470, fld, "limits-lines" if fld else None)
        y -= 15
    para(p, 54, y - 20, BOILER)
    p2 = d.page()
    header(p2, ins, "OCM-GL-131225", "OCM GL DEC 12 25", "Page 2 of 3", title="SCHEDULE OF FORMS AND ENDORSEMENTS")
    rows = [["Form", "Edition", "Title"],
            ["OCM CG 00 01", "04 13", "Commercial General Liability Coverage Form"],
            ["OCM CG 20 10", "12 19", "Additional Insured - Owners, Lessees or Contractors"],
            ["OCM CG 21 06", "05 14", "Exclusion - Access or Disclosure of Confidential Information"],
            ["OCM IL 00 21", "09 08", "Nuclear Energy Liability Exclusion"]]
    table(p2, 54, 700, [100, 60, 344], rows, "forms-table", rh=18)
    p3 = d.page()
    header(p3, ins, "OCM-GL-131225", "OCM GL DEC 12 25", "Page 3 of 3", title="POLICY TERM AND PREMIUM")
    p3.text(54, 700, "Policy Period:", "Helvetica-Bold", 9)
    x = p3.text(130, 700, PS, "Helvetica", 9, field=F_PS, region="term-line")
    x = p3.text(x + 4, 700, "to", "Helvetica", 9)
    p3.text(x + 4, 700, PE, "Helvetica", 9, field=F_PE, region="term-line")
    kv(p3, 54, 684, "Date Issued:", "December 4, 2025", 76)
    kv(p3, 54, 668, "Advance Premium:", "$9,240", 96)
    return d


BUILDERS = [doc_001, doc_002, doc_003, doc_004, doc_005, doc_006, doc_007,
            doc_008, doc_009, doc_010, doc_011, doc_012, doc_013]


# --------------------------------------------------------------------------- rendering


def _draw_ops(c, ops):
    for op in ops:
        kind = op[0]
        if kind == "text":
            _, x, y, s, font, size = op
            c.setFillGray(0)
            c.setFont(font, size)
            c.drawString(x, y, s)
        elif kind == "rect":
            _, x, y, w, h, fill, lw = op
            if fill is not None:
                c.setFillGray(fill)
                c.rect(x, y, w, h, stroke=0, fill=1)
            if lw:
                c.setLineWidth(lw)
                c.setStrokeGray(0)
                c.rect(x, y, w, h, stroke=1, fill=0)
        elif kind == "line":
            _, x1, y1, x2, y2, lw = op
            c.setLineWidth(lw)
            c.setStrokeGray(0)
            c.line(x1, y1, x2, y2)
        elif kind == "image":
            _, x, y, w, h, region = op
            img = _rasterize_surface(region, REGION_DPI)
            c.drawImage(ImageReader(img), x, y, w, h)
        else:
            raise ValueError(kind)


def _new_canvas(buf, size, title):
    c = canvas.Canvas(buf, pagesize=size, pageCompression=1, invariant=1)
    c.setTitle(title)
    c.setAuthor("")
    c.setSubject("")
    c.setCreator("")
    return c


def _rasterize_surface(surface, dpi):
    buf = io.BytesIO()
    c = _new_canvas(buf, (surface.w, surface.h), "region")
    _draw_ops(c, surface.ops)
    c.showPage()
    c.save()
    pdf = pdfium.PdfDocument(buf.getvalue())
    try:
        img = pdf[0].render(scale=dpi / 72.0, grayscale=True).to_pil().convert("L")
    finally:
        pdf.close()
    return img


def render_native(doc) -> bytes:
    buf = io.BytesIO()
    c = _new_canvas(buf, (PAGE_W, PAGE_H), "Commercial General Liability Declarations")
    for pg in doc.pages:
        _draw_ops(c, pg.ops)
        c.showPage()
    c.save()
    return buf.getvalue()


def _degrade(img, rng):
    """Light scanner artefacts: skew, speckle, slight blur and paper tone. Stays legible."""
    angle = rng.uniform(-0.6, 0.6)
    img = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=255)
    px = img.load()
    w, h = img.size
    for _ in range(rng.randint(900, 1600)):
        x, y = rng.randrange(w), rng.randrange(h)
        px[x, y] = rng.choice((40, 80, 120, 160))
    img = img.filter(ImageFilter.GaussianBlur(0.35))
    tone = rng.randint(238, 248)
    return img.point(lambda v: v * tone // 255)


def render_scanned(doc, native_pdf: bytes) -> bytes:
    rng = random.Random(doc.seed)
    pdf = pdfium.PdfDocument(native_pdf)
    jpegs = []
    try:
        for i in range(len(pdf)):
            img = pdf[i].render(scale=SCAN_DPI / 72.0, grayscale=True).to_pil().convert("L")
            img = _degrade(img, rng)
            jb = io.BytesIO()
            img.save(jb, format="JPEG", quality=82, optimize=False, progressive=False)
            jpegs.append(jb.getvalue())
    finally:
        pdf.close()
    buf = io.BytesIO()
    c = _new_canvas(buf, (PAGE_W, PAGE_H), "Commercial General Liability Declarations")
    for jb in jpegs:
        c.drawImage(ImageReader(io.BytesIO(jb)), 0, 0, PAGE_W, PAGE_H)
        c.showPage()
    c.save()
    return buf.getvalue()


def damage_page(pdf_bytes: bytes, page_index: int) -> bytes:
    """Overwrite one page's content-stream body with same-length garbage.

    Lengths and xref offsets are unchanged, so the file structure stays valid and the
    other pages remain readable; the damaged page's filter chain cannot decode.
    The page's content object number is located from reportlab's own single /Pages
    node (/Kids order) and the page dict's leading '/Contents N 0 R' entry.
    """
    kids = re.findall(rb"/Kids \[([^\]]*)\]", pdf_bytes)
    assert len(kids) == 1, "expected a single /Pages node"
    page_objs = [int(n) for n in re.findall(rb"(\d+) 0 R", kids[0])]
    pm = re.search(rb"\n%d 0 obj\n<<\n/Contents (\d+) 0 R" % page_objs[page_index], pdf_bytes)
    assert pm, "page object not found"
    target = int(pm.group(1))
    m = re.search(rb"\n%d 0 obj\n.*?stream\r?\n" % target, pdf_bytes, re.S)
    assert m, "content object not found"
    start = m.end()
    end = pdf_bytes.index(b"endstream", start)
    body_len = end - start
    garbage = bytes((0x80 + (i * 37) % 0x7F) for i in range(body_len - 1)) + b"\n"
    return pdf_bytes[:start] + garbage + pdf_bytes[end:]


# --------------------------------------------------------------------------- outputs


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _y(s) -> str:
    return json.dumps(s, ensure_ascii=False)


def write_corpus_yaml(entries):
    lines = [
        "# GENERATED by build_corpus.py - do not edit by hand.",
        f"label: {_y(LABEL)}",
        "synthetic: true",
        f"corpus_id: {_y(CORPUS_ID)}",
        'generator: "build_corpus.py"',
        "location_note: \"neuron/fixtures/qualification/ - outside golden-corpus/ and the frozen holdout\"",
        "profiles:",
    ]
    for pname, fields in PROFILES.items():
        lines.append(f"  {pname}: [{', '.join(fields)}]")
    lines.append(f"case_tags: [{', '.join(TAGS)}]")
    lines.append("documents:")
    for e in entries:
        d = e["doc"]
        lines += [
            f"  - id: {d.doc_id}",
            f"    kind: {d.kind}",
            f"    file: documents/{d.doc_id}.pdf",
            f"    expectations: expectations/{d.doc_id}.json",
            f"    pages: {len(d.pages)}",
            f"    layout: {_y(d.layout)}",
            f"    date_format: {_y(d.date_format)}",
            f"    text_layer: {_y(e['text_layer'])}",
            f"    damaged_pages: [{', '.join(str(x) for x in d.damaged_pages)}]",
            f"    seed: {d.seed}",
            "    case_tags:",
        ]
        for f in FIELDS:
            lines.append(f"      {f}: [{', '.join(d.tags[f])}]")
        lines.append(f"    sha256: {e['pdf_sha']}")
    (HERE / "corpus.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def coverage(docs):
    cov = {f: {t: [] for t in TAGS} for f in FIELDS}
    for d in docs:
        for f in FIELDS:
            for t in d.tags[f]:
                cov[f][t].append(d.doc_id.replace("gl-q-", ""))
    return cov


def write_readme(docs, cov):
    rows = ["| field | " + " | ".join(TAGS) + " |", "|---|" + "---|" * len(TAGS)]
    for f in FIELDS:
        rows.append(f"| `{f}` | " + " | ".join(", ".join(cov[f][t]) for t in TAGS) + " |")
    inv = ["| id | kind | pages | layout | damaged page |", "|---|---|---|---|---|"]
    for d in docs:
        inv.append(f"| {d.doc_id} | {d.kind} | {len(d.pages)} | {d.layout} | "
                   f"{', '.join(map(str, d.damaged_pages)) or '-'} |")
    text = f"""# F0005 qualification corpus (synthetic development data)

**Synthetic development data.** Thirteen fictional US commercial general liability
declarations documents with independently authored expected values for the
`gl-limits-a` and `gl-limits-b` extraction profiles. Every name, address, policy number
and form number is invented. This corpus is not `golden-corpus/` and not the frozen holdout.

## Regenerate

From the product repo root:

```
neuron/.venv/bin/python neuron/fixtures/qualification/build_corpus.py
cd neuron/fixtures/qualification && sha256sum -c CORPUS-HASHES.txt
```

The generator is deterministic (fixed seeds, `reportlab.rl_config.invariant = 1`,
fixed JPEG settings), so a rerun reproduces every file byte for byte. It deletes and
rewrites `documents/` and `expectations/`, and rewrites `corpus.yaml`,
`CORPUS-HASHES.txt` and this README.

## Contents

- 6 `native` documents (text layer), 4 `scanned` documents (each page is a
  {SCAN_DPI} dpi grayscale JPEG with slight skew and speckle, and no text layer),
  2 `mixed` documents (text layer plus one pixel-only image region holding some
  expected values), and 1 `partial` document (text layer; page 2 has a corrupted
  content stream and holds no expected values).
- Distractors in every document: Products-Completed Operations Aggregate, Personal and
  Advertising Injury, Damage to Premises Rented, Medical Expense, issue/retroactive
  dates, producer/insurer/additional-insured names. A distractor amount never
  equals the target value in the same document.
- `expectations/<id>.json` holds, for each profile field, `value` (verbatim as printed,
  or `null` when absent) and `evidence` (`page`, exact printed `text`, `region`).
  A `split-across-regions` value is the two printed parts joined by one space, and both
  parts are listed as evidence.

{chr(10).join(inv)}

## Case-tag coverage (document numbers, gl-q-NNN)

{chr(10).join(rows)}

Every field x tag cell is non-empty. Per-document tags are in `corpus.yaml`.

## Independence

`build_corpus.py` takes expected values from its own layout specifications only. It
does not import, run or read any conversion or extraction code (Docling,
docling-graph, brain_extraction, brain_ingestion, model servers). pypdf is used only
outside the generator, to check text-layer presence and the damaged page.
"""
    (HERE / "README.md").write_text(text, encoding="utf-8")


def main():
    for dd in (DOC_DIR, EXP_DIR):
        if dd.exists():
            shutil.rmtree(dd)
        dd.mkdir(parents=True)
    docs, entries, hash_lines = [], [], []
    for build in BUILDERS:
        d = build()
        d.validate()
        native = render_native(d)
        if d.kind == "scanned":
            pdf, layer = render_scanned(d, native), "none (image-only pages)"
        elif d.kind == "mixed":
            pdf, layer = native, "partial (one pixel-only image region)"
        elif d.kind == "partial":
            pdf = native
            for pnum in d.damaged_pages:
                pdf = damage_page(pdf, pnum - 1)
            layer = f"yes, except damaged page(s) {d.damaged_pages}"
        else:
            pdf, layer = native, "yes"
        pdf_path = DOC_DIR / f"{d.doc_id}.pdf"
        pdf_path.write_bytes(pdf)
        exp = json.dumps(d.expectation_json(), indent=2, ensure_ascii=False) + "\n"
        exp_path = EXP_DIR / f"{d.doc_id}.json"
        exp_path.write_bytes(exp.encode("utf-8"))
        docs.append(d)
        entries.append({"doc": d, "pdf_sha": sha256(pdf), "text_layer": layer})
        hash_lines.append(f"{sha256(pdf)}  documents/{d.doc_id}.pdf")
        hash_lines.append(f"{sha256(exp.encode('utf-8'))}  expectations/{d.doc_id}.json")
    cov = coverage(docs)
    missing = [(f, t) for f in FIELDS for t in TAGS if not cov[f][t]]
    assert not missing, f"coverage gaps: {missing}"
    kinds = [d.kind for d in docs]
    assert (kinds.count("native"), kinds.count("scanned"), kinds.count("mixed"), kinds.count("partial")) == (6, 4, 2, 1)
    write_corpus_yaml(entries)
    write_readme(docs, cov)
    (HERE / "CORPUS-HASHES.txt").write_text("\n".join(sorted(hash_lines, key=lambda s: s[66:])) + "\n")
    print(f"wrote {len(docs)} documents to {DOC_DIR}")


if __name__ == "__main__":
    main()

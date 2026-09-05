#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "Pillow==11.0.0",
#   "reportlab==5.0.1",
# ]
# ///
"""Build the YouKnow Shop images and render-checked PDF manual source."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as PdfImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


DOCS = Path(__file__).resolve().parent
PROJECT = DOCS.parent
OUTPUT = PROJECT / "Release"
PDF_OUTPUT = OUTPUT / "pdf"
SHOP_OUTPUT = OUTPUT / "shop"
GUIDE = DOCS / "USER_GUIDE.md"
SHOP_COPY = DOCS / "SHOP_COPY.md"
LICENSE = PROJECT / "LICENSE"
PRIVACY = PROJECT / "PRIVACY.md"
THIRD_PARTY = PROJECT / "THIRD_PARTY_NOTICES.md"
MANUAL = PDF_OUTPUT / "YouKnow_User_Manual.pdf"

INFO = (PROJECT / "info.lua").read_text(encoding="utf-8")
VERSION_MATCH = re.search(r'^version_number\s*=\s*"([^"]+)"', INFO, re.MULTILINE)
assert VERSION_MATCH, "info.lua has no version_number"
RAW_VERSION = VERSION_MATCH.group(1)
VERSION = RAW_VERSION
INK = "#eef1f1"
MUTED = "#b8c4ca"
ICE = "#6ec1d4"
RED = "#e1775c"
DARK = "#151c21"


def validate_shop_copy():
    markdown = SHOP_COPY.read_text(encoding="utf-8")
    assert re.search(
        rf"^- Candidate: `{re.escape(RAW_VERSION)}`$", markdown, re.MULTILINE
    ), "Shop candidate version differs from info.lua"
    article = re.search(r"^- Article: (.+)$", markdown, re.MULTILINE)
    assert article and RAW_VERSION in article.group(1), (
        "Shop article version differs from info.lua"
    )
    guide = GUIDE.read_text(encoding="utf-8")
    assert re.search(
        rf"^Version {re.escape(RAW_VERSION)}$", guide, re.MULTILINE
    ), "user-guide version differs from info.lua"

    long_title_match = re.search(
        r"^- Long title: (.+?) \(\d+ characters\)$", markdown, re.MULTILINE
    )
    assert long_title_match, "Shop copy has no measured long title"
    assert len(long_title_match.group(1)) <= 22, "Shop long title exceeds 22 characters"

    feature_block = re.search(
        r"^## Top features\n\n(.+?)\n\n## Short description$",
        markdown,
        re.MULTILINE | re.DOTALL,
    )
    assert feature_block, "Shop copy has no top-feature block"
    features = [
        re.sub(r" \(\d+ characters\)$", "", line[2:])
        for line in feature_block.group(1).splitlines()
        if line.startswith("- ")
    ]
    assert len(features) == 3, "Shop copy must have exactly three top features"
    assert all(len(feature) <= 50 for feature in features), (
        "Shop top feature exceeds 50 characters"
    )

    short_match = re.search(
        r"^## Short description\n\n(.+?)\n\nLength:",
        markdown,
        re.MULTILINE | re.DOTALL,
    )
    assert short_match, "Shop copy has no short description"
    short_description = " ".join(short_match.group(1).split())
    assert len(short_description) <= 275, "Shop short description exceeds 275 characters"

    for field in ("Article", "Price category", "Upgrade price category", "Tags"):
        assert re.search(rf"^- {field}: .+$", markdown, re.MULTILINE), (
            f"Shop copy has no {field.lower()} decision"
        )


def notices_markdown():
    privacy = PRIVACY.read_text(encoding="utf-8").replace(
        "# Privacy notice", "## Privacy notice", 1
    )
    third_party = THIRD_PARTY.read_text(encoding="utf-8").replace(
        "# Third-party notices and provenance",
        "## Third-party notices and provenance",
        1,
    )
    return "\n\n".join((
        "## Protocodus source-component MIT license\n\n"
        "This notice applies only to Protocodus-authored source and artwork. "
        "It does not relicense Reason SDK material. Shop delivery is governed "
        "by Reason Studios' applicable "
        "customer terms.\n\n"
        + LICENSE.read_text(encoding="utf-8"),
        privacy,
        third_party,
    ))


def load_panel_renderer():
    path = PROJECT / "Design" / "render_panels.py"
    spec = spec_from_file_location("youknow_panels", path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def composed_panels():
    panels = load_panel_renderer()
    panels.main()
    assets = {
        name: Image.open(panels.OUT / f"{name}.png").convert("RGBA")
        for name in (
            "Fader", "Knob", "Toggle", "MomentaryOverlay", "Lamp",
            "PitchWheel", "ModWheel", "AudioJack", "CVJack", "TapeHorz",
            "TapeVert", "Placeholder",
        )
    }
    front_panel = Image.open(
        panels.OUT / "Reason_GUI_front_root_Panel.png"
    ).convert("RGBA")
    back_panel = Image.open(
        panels.OUT / "Reason_GUI_back_root_Panel.png"
    ).convert("RGBA")
    return (
        panels,
        panels.composite_front(front_panel, assets),
        panels.composite_back(back_panel, assets),
    )


def fit(image, maximum):
    copy = image.copy()
    copy.thumbnail(maximum, Image.Resampling.LANCZOS)
    return copy


def build_shop_images(panels, front, back):
    SHOP_OUTPUT.mkdir(parents=True, exist_ok=True)
    front_shop = fit(front.convert("RGB"), (1600, 1200))
    back_shop = fit(back.convert("RGB"), (1600, 1200))
    front_path = SHOP_OUTPUT / "YouKnow_Front.png"
    back_path = SHOP_OUTPUT / "YouKnow_Back.png"
    front_shop.save(front_path, optimize=True)
    back_shop.save(back_path, optimize=True)

    thumbnail = Image.new("RGB", (800, 800), DARK)
    glow = Image.new("RGBA", thumbnail.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((95, 120, 705, 730), fill=(102, 188, 216, 28))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    thumbnail = Image.alpha_composite(thumbnail.convert("RGBA"), glow)
    draw = ImageDraw.Draw(thumbnail)
    display = ImageFont.truetype(str(panels.DISPLAY_FONT), 74)
    label = ImageFont.truetype(str(panels.LABEL_FONT), 24)
    small = ImageFont.truetype(str(panels.SECTION_FONT), 24)
    draw.text((42, 32), "PROTOCODUS", font=small, fill=ICE)
    draw.text((40, 62), "YOUKNOW", font=display, fill=INK)
    draw.text((43, 143), "CIRCUIT-MODELLED SYNTH FOR REASON",
              font=label, fill=MUTED)
    device = fit(front.convert("RGBA"), (760, 556))
    x = (800 - device.width) // 2
    y = 188
    shadow = Image.new("RGBA", thumbnail.size, (0, 0, 0, 0))
    shadow.alpha_composite(
        Image.new("RGBA", device.size, (0, 0, 0, 180)), (x + 8, y + 12)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    thumbnail = Image.alpha_composite(thumbnail, shadow)
    thumbnail.alpha_composite(device, (x, y))
    draw = ImageDraw.Draw(thumbnail)
    draw.rectangle((40, 764, 760, 768), fill=RED)
    thumb_path = SHOP_OUTPUT / "YouKnow_Thumbnail_800.png"
    thumbnail.convert("RGB").save(thumb_path, optimize=True)

    assert front_shop.width <= 1600 and front_shop.height <= 1200
    assert back_shop.width <= 1600 and back_shop.height <= 1200
    assert Image.open(thumb_path).size == (800, 800)
    return front_path, back_path, thumb_path


def inline_markup(text):
    value = escape(text)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", value)

    def link(match):
        label, target = match.groups()
        if not re.match(r"(?:https?://|mailto:)", target):
            return label
        return f'<link href="{target}" color="#246b80">{label}</link>'

    value = re.sub(r"\[([^]]+)\]\(([^)]+)\)", link, value)
    value = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', value)
    return value


def markdown_flowables(markdown, styles, back_image):
    lines = markdown.splitlines()
    first_section = next(i for i, line in enumerate(lines) if line.startswith("## "))
    lines = lines[first_section:]
    story = []
    paragraph = []
    list_item = []
    list_marker = None

    def flush():
        nonlocal list_marker
        if list_item:
            story.append(Paragraph(
                inline_markup(" ".join(list_item)), styles["BulletYK"],
                bulletText=list_marker,
            ))
            story.append(Spacer(1, 1.2 * mm))
            list_item.clear()
            list_marker = None
        if paragraph:
            story.append(Paragraph(inline_markup(" ".join(paragraph)), styles["BodyYK"]))
            story.append(Spacer(1, 2.3 * mm))
            paragraph.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith("## "):
            flush()
            title = stripped[3:]
            if title == "Rear panel and engine quality":
                story.append(PageBreak())
            story.append(Spacer(1, 2.5 * mm))
            story.append(Paragraph(inline_markup(title), styles["HeadingYK"]))
            if title == "Rear panel and engine quality":
                story.append(Spacer(1, 2 * mm))
                story.append(PdfImage(
                    str(back_image), width=176 * mm, height=128.9 * mm
                ))
                story.append(Spacer(1, 3 * mm))
            continue
        bullet = re.match(r"^-\s+(.*)$", stripped)
        numbered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if bullet or numbered:
            flush()
            list_marker = "-" if bullet else numbered.group(1) + "."
            list_item.append(bullet.group(1) if bullet else numbered.group(2))
            continue
        (list_item if list_item else paragraph).append(stripped)
    flush()
    return story


def build_manual(front_image, back_image):
    PDF_OUTPUT.mkdir(parents=True, exist_ok=True)
    markdown = GUIDE.read_text(encoding="utf-8")
    forbidden_dashes = {"\u2010", "\u2011", "\u2012", "\u2013", "\u2014"}
    assert forbidden_dashes.isdisjoint(markdown), "manual source must use ASCII hyphens"

    rl_config.invariant = 1
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CoverBrand", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=14, leading=17, textColor=colors.HexColor("#347587"), spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=34, leading=36, textColor=colors.HexColor("#202323"),
        spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        name="CoverSub", parent=styles["Normal"], fontName="Helvetica",
        fontSize=12, leading=16, textColor=colors.HexColor("#555b59"),
        spaceAfter=7 * mm,
    ))
    styles.add(ParagraphStyle(
        name="HeadingYK", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=17, leading=20, textColor=colors.HexColor("#252827"),
        spaceBefore=2 * mm, spaceAfter=3.5 * mm, keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="BodyYK", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=9.5, leading=14, spaceBefore=0, allowWidows=0, allowOrphans=0,
        textColor=colors.HexColor("#343837"),
    ))
    styles.add(ParagraphStyle(
        name="BulletYK", parent=styles["BodyYK"], leftIndent=7 * mm,
        firstLineIndent=0, bulletIndent=1.5 * mm, bulletFontName="Helvetica-Bold",
        bulletColor=colors.HexColor(RED),
    ))

    doc = SimpleDocTemplate(
        str(MANUAL), pagesize=A4, rightMargin=17 * mm, leftMargin=17 * mm,
        topMargin=15 * mm, bottomMargin=16 * mm, title="YouKnow User Guide",
        author="Protocodus", subject=f"YouKnow {VERSION} user guide",
        pageCompression=1,
    )

    def page(canvas, document):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#777d7a"))
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(17 * mm, 9 * mm, f"YouKnow {VERSION} | Protocodus")
        canvas.drawRightString(A4[0] - 17 * mm, 9 * mm, str(document.page))
        if document.page > 1:
            canvas.setStrokeColor(colors.HexColor(ICE))
            canvas.setLineWidth(0.6)
            canvas.line(17 * mm, A4[1] - 10.5 * mm,
                        A4[0] - 17 * mm, A4[1] - 10.5 * mm)
        canvas.restoreState()

    story = [
        Spacer(1, 8 * mm),
        Paragraph("PROTOCODUS", styles["CoverBrand"]),
        Paragraph("YouKnow", styles["CoverTitle"]),
        Paragraph(
            f"Circuit-Modelled Synth for Reason 14+<br/>User Guide - {VERSION}",
            styles["CoverSub"],
        ),
        PdfImage(str(front_image), width=176 * mm, height=128.9 * mm),
        Spacer(1, 6 * mm),
        Paragraph(
            "Direct subtractive synthesis, 77 original patches, polyphonic "
            "MIDI, monophonic Note/Gate CV, stereo chorus, and scalable "
            "rear-panel engine quality.",
            styles["BodyYK"],
        ),
        PageBreak(),
    ]
    story.extend(markdown_flowables(markdown, styles, back_image))
    story.extend(markdown_flowables(notices_markdown(), styles, back_image))
    doc.build(story, onFirstPage=page, onLaterPages=page)
    assert MANUAL.stat().st_size > 100_000, "manual PDF unexpectedly small"


def main():
    validate_shop_copy()
    panels, front, back = composed_panels()
    front_path, back_path, thumbnail_path = build_shop_images(panels, front, back)
    build_manual(front_path, back_path)
    print(f"YouKnow release materials: {front_path}, {back_path}, {thumbnail_path}, {MANUAL}")


if __name__ == "__main__":
    main()

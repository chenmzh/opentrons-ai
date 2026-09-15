"""Embed a compact, searchable CJK font subset in the Chinese article."""

import base64
import subprocess


def chinese_font_css(text, output):
    from fontTools import subset
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.scaleUpem import scale_upem

    match = subprocess.check_output(
        ["fc-match", "-f", "%{file}\\n%{index}\\n", "Noto Sans CJK SC"], text=True
    ).splitlines()
    font = TTFont(match[0], fontNumber=int(match[1]))
    missing = {c for c in text if "\u4e00" <= c <= "\u9fff" and ord(c) not in font.getBestCmap()}
    if missing:
        raise RuntimeError("Install Noto Sans CJK before building the Chinese report")
    options = subset.Options()
    options.layout_features = []
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    glyph_set = font.getGlyphSet()
    glyphs = {}
    for name in font.getGlyphOrder():
        pen = TTGlyphPen(None)
        glyph_set[name].draw(Cu2QuPen(pen, 1.0, reverse_direction=True))
        glyphs[name] = pen.glyph()
    builder = FontBuilder(font["head"].unitsPerEm, isTTF=True)
    builder.setupGlyphOrder(font.getGlyphOrder())
    builder.setupCharacterMap(font.getBestCmap())
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(font["hmtx"].metrics)
    builder.setupHorizontalHeader(ascent=font["hhea"].ascent, descent=font["hhea"].descent)
    builder.setupNameTable(
        {
            "familyName": "Research Sans",
            "styleName": "Regular",
            "uniqueFontIdentifier": "ResearchSans-Subset",
            "fullName": "Research Sans",
            "psName": "ResearchSans-Subset",
            "version": "Version 1.0",
            "copyright": font["name"].getDebugName(0) or "Noto font contributors",
            "licenseDescription": font["name"].getDebugName(13) or "SIL Open Font License 1.1",
            "licenseInfoURL": font["name"].getDebugName(14) or "https://openfontlicense.org",
        }
    )
    builder.setupOS2(
        sTypoAscender=font["OS/2"].sTypoAscender,
        sTypoDescender=font["OS/2"].sTypoDescender,
        usWinAscent=font["OS/2"].usWinAscent,
        usWinDescent=font["OS/2"].usWinDescent,
    )
    builder.setupPost()
    # A 256-unit grid bounds body-text coordinate quantization to about 0.04 pt
    # at 10 pt. Plot geometry and the numerical evidence are not transformed.
    scale_upem(builder.font, 256)
    path = output / "research-sans.ttf"
    builder.save(path)
    encoded = base64.b64encode(path.read_bytes()).decode()
    return (
        "@font-face {font-family:'Research Sans';src:url(data:font/ttf;base64,"
        + encoded
        + ");} body, body * {font-family:'Research Sans',sans-serif;"
        "font-weight:400;font-synthesis:none;}"
    )

from pathlib import Path
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "中美外语院系英文简介_5分钟汇报.pptx"
PREVIEW = ROOT / "previews"
PREVIEW.mkdir(parents=True, exist_ok=True)

SLIDE_W, SLIDE_H = 13.333, 7.5
PX_PER_IN = 120
FONT_REG = "/tmp/ppt-fonts/expo/package/400Regular/NotoSansSC_400Regular.ttf"
FONT_BOLD = "/tmp/ppt-fonts/expo/package/700Bold/NotoSansSC_700Bold.ttf"

NAVY = "17324D"
BLUE = "3568A8"
ORANGE = "E38B36"
TEAL = "2B7A78"
TEXT = "23364A"
MUTED = "62748A"
PALE = "F7F9FC"
PALE_BLUE = "EAF1F8"
PALE_ORANGE = "FFF3E5"
WHITE = "FFFFFF"
LINE = "D8E1EB"


def rgb(hex_color):
    return RGBColor.from_string(hex_color)


def pil_rgb(hex_color):
    return "#" + hex_color


@lru_cache(maxsize=64)
def preview_font(size_px, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size_px)


class Canvas:
    def __init__(self, prs, slide, image):
        self.prs = prs
        self.slide = slide
        self.image = image
        self.draw = ImageDraw.Draw(image)

    @staticmethod
    def px(v):
        return int(round(v * PX_PER_IN))

    def rect(self, x, y, w, h, fill, line=None, radius=0, width=1):
        kind = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
        shape = self.slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(fill)
        if line:
            shape.line.color.rgb = rgb(line)
            shape.line.width = Pt(width)
        else:
            shape.line.fill.background()
        box = [self.px(x), self.px(y), self.px(x + w), self.px(y + h)]
        if radius:
            self.draw.rounded_rectangle(box, radius=self.px(radius), fill=pil_rgb(fill), outline=pil_rgb(line) if line else None, width=max(1, self.px(width / 72)))
        else:
            self.draw.rectangle(box, fill=pil_rgb(fill), outline=pil_rgb(line) if line else None, width=max(1, self.px(width / 72)))
        return shape

    def circle(self, x, y, d, fill, line=None, width=1):
        shape = self.slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
        shape.fill.solid(); shape.fill.fore_color.rgb = rgb(fill)
        if line:
            shape.line.color.rgb = rgb(line); shape.line.width = Pt(width)
        else:
            shape.line.fill.background()
        self.draw.ellipse([self.px(x), self.px(y), self.px(x + d), self.px(y + d)], fill=pil_rgb(fill), outline=pil_rgb(line) if line else None)
        return shape

    def line(self, x1, y1, x2, y2, color=LINE, width=1):
        shape = self.slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        shape.line.color.rgb = rgb(color); shape.line.width = Pt(width)
        self.draw.line([self.px(x1), self.px(y1), self.px(x2), self.px(y2)], fill=pil_rgb(color), width=max(1, self.px(width / 72)))
        return shape

    def text(self, x, y, w, h, text, size=16, color=TEXT, bold=False,
             align="left", valign="top", font="Microsoft YaHei", spacing=1.12):
        box = self.slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = box.text_frame
        tf.clear(); tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE, "bottom": MSO_ANCHOR.BOTTOM}[valign]
        lines = text.split("\n")
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = line
            p.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[align]
            p.space_after = Pt(0); p.space_before = Pt(0)
            for run in p.runs:
                run.font.name = font; run.font.size = Pt(size); run.font.bold = bold; run.font.color.rgb = rgb(color)
        f = preview_font(max(1, self.px(size / 72)), bold)
        line_h = self.px(size / 72) * spacing
        total_h = line_h * len(lines)
        if valign == "middle":
            ty = self.px(y) + (self.px(h) - total_h) / 2
        elif valign == "bottom":
            ty = self.px(y + h) - total_h
        else:
            ty = self.px(y)
        for line in lines:
            bbox = self.draw.textbbox((0, 0), line, font=f)
            tw = bbox[2] - bbox[0]
            if align == "center":
                tx = self.px(x) + (self.px(w) - tw) / 2
            elif align == "right":
                tx = self.px(x + w) - tw
            else:
                tx = self.px(x)
            self.draw.text((tx, ty), line, font=f, fill=pil_rgb(color))
            ty += line_h
        return box


class Deck:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width = Inches(SLIDE_W)
        self.prs.slide_height = Inches(SLIDE_H)
        self.prs.core_properties.title = "基于语料库技术的中美外语院系英文简介话语比较分析"
        self.prs.core_properties.subject = "本科生创新训练培育项目中期汇报"
        self.prs.core_properties.author = "项目组"
        self.slide_no = 0

    def add_slide(self, bg=PALE):
        self.slide_no += 1
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        image = Image.new("RGB", (self.px(SLIDE_W), self.px(SLIDE_H)), pil_rgb(bg))
        canvas = Canvas(self.prs, slide, image)
        canvas.rect(0, 0, SLIDE_W, SLIDE_H, bg)
        return canvas

    @staticmethod
    def px(v):
        return int(round(v * PX_PER_IN))

    def save_slide(self, canvas):
        canvas.image.save(PREVIEW / f"slide_{self.slide_no:02d}.png", quality=95)

    def save(self):
        self.prs.save(OUT)
        print(OUT)


def slide_01(deck):
    c = deck.add_slide()
    c.rect(0, 0, 0.16, SLIDE_H, NAVY)
    c.rect(0.16, 0, 0.055, 1.35, ORANGE)
    c.rect(0.76, 0.52, 3.75, 0.42, NAVY, radius=0.10)
    c.text(0.92, 0.52, 3.43, 0.42, "本科生创新训练培育项目｜中期汇报", 12, WHITE, bold=True, valign="middle")

    c.text(0.78, 1.40, 7.75, 2.12, "基于语料库技术的\n中美外语院系英文简介\n话语比较分析", 30, NAVY, bold=True, spacing=1.28)
    c.text(0.80, 3.76, 7.65, 0.50, "中美高校外语院系英文 About Us 文本的语料库辅助比较", 15, MUTED, valign="middle")
    c.rect(0.80, 4.35, 0.65, 0.045, ORANGE)

    cards = [(0.80, "60", "个院系文本"), (2.86, "30＋30", "中美样本"), (5.15, "10", "核心语步")]
    widths = [1.78, 2.02, 1.78]
    for (x, number, label), w in zip(cards, widths):
        c.rect(x, 4.68, w, 1.03, WHITE, line=LINE, radius=0.10, width=0.8)
        c.text(x, 4.78, w, 0.47, number, 23, BLUE, bold=True, align="center", valign="middle")
        c.text(x, 5.28, w, 0.28, label, 11, MUTED, align="center", valign="middle")

    # Right-side editable visual: a browser card and three research stages.
    c.rect(9.00, 0.95, 3.55, 5.40, PALE_BLUE, radius=0.18)
    c.rect(9.34, 1.36, 2.87, 1.47, WHITE, line=LINE, radius=0.10, width=0.8)
    for i, color in enumerate([ORANGE, BLUE, TEAL]):
        c.circle(9.53 + i * 0.18, 1.55, 0.085, color)
    c.text(9.54, 1.80, 2.46, 0.38, "About Us", 19, NAVY, bold=True)
    c.rect(9.55, 2.28, 2.18, 0.055, LINE, radius=0.02)
    c.rect(9.55, 2.45, 1.62, 0.055, LINE, radius=0.02)

    c.text(9.36, 3.09, 2.80, 0.30, "研究路径", 11, MUTED, bold=True)
    stages = [(3.48, "01", "语步分布", BLUE), (4.20, "02", "语言实现", TEAL), (4.92, "03", "语境解释", ORANGE)]
    for y, num, label, color in stages:
        c.rect(9.34, y, 2.87, 0.56, WHITE, radius=0.09)
        c.circle(9.50, y + 0.11, 0.34, color)
        c.text(9.50, y + 0.11, 0.34, 0.34, num, 9, WHITE, bold=True, align="center", valign="middle")
        c.text(10.02, y + 0.04, 1.88, 0.48, label, 15, NAVY, bold=True, valign="middle")
    c.text(9.36, 5.78, 2.82, 0.28, "MOVE · LANGUAGE · CONTEXT", 8, MUTED, align="center")

    c.line(0.80, 6.30, 12.55, 6.30, LINE, 0.8)
    c.text(0.80, 6.52, 3.00, 0.34, "外语学院", 13, NAVY, bold=True)
    c.text(0.80, 6.93, 6.60, 0.30, "汇报人：________　　指导教师：________", 11, MUTED)
    c.text(10.60, 6.90, 1.20, 0.30, "2026年", 11, MUTED, align="right")
    c.text(11.90, 6.90, 0.65, 0.30, "01 / 07", 10, MUTED, align="right")
    deck.save_slide(c)


def main():
    deck = Deck()
    slide_01(deck)
    deck.save()


if __name__ == "__main__":
    main()

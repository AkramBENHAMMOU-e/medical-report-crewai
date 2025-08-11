import os
import re
import tempfile
from datetime import datetime
from typing import List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepInFrame


class ModernPDFGenerator:
    """Générateur PDF professionnel, multi-pages, 2 couleurs, avec logo PsyChat.

    - Titre 24pt, sections 18pt, texte 14pt (leading 20) pour une lisibilité optimale
    - Nettoie placeholders [À compléter], lignes système, doublons de titre
    - Rendu propre: titres, listes, paragraphes, gras/italique/code
    - Sans tableaux, multi-pages si nécessaire
    """

    def __init__(self) -> None:
        # Couleurs (2 couleurs)
        self.primary_blue = HexColor("#2B6CB0")
        self.dark_text = HexColor("#111827")

        # Styles
        self.styles = getSampleStyleSheet()
        self._setup_styles()

        # Logo
        self.logo_path = self._find_logo_path()

    # ---------------- Utils ----------------
    def _find_logo_path(self) -> Optional[str]:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        candidates = [
            os.path.join(base_dir, "frontend", "public", "logoPsyChat.png"),
            os.path.join(base_dir, "medical_report", "frontend", "public", "logoPsyChat.png"),
            os.path.join(os.getcwd(), "medical_report", "frontend", "public", "logoPsyChat.png"),
            os.path.join(os.getcwd(), "frontend", "public", "logoPsyChat.png"),
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return None

    def _setup_styles(self) -> None:
        self.styles.add(ParagraphStyle(
            name="ReportTitle", parent=self.styles["Title"], fontSize=24, leading=28,
            textColor=self.dark_text, alignment=TA_LEFT, spaceAfter=8, fontName="Helvetica-Bold"
        ))
        self.styles.add(ParagraphStyle(
            name="ReportSubtitle", parent=self.styles["Heading2"], fontSize=16, leading=20,
            textColor=self.primary_blue, alignment=TA_LEFT, spaceAfter=12, fontName="Helvetica"
        ))
        self.styles.add(ParagraphStyle(
            name="SectionHeader", parent=self.styles["Heading2"], fontSize=18, leading=22,
            textColor=self.primary_blue, alignment=TA_LEFT, spaceBefore=12, spaceAfter=8, fontName="Helvetica-Bold"
        ))
        self.styles.add(ParagraphStyle(
            name="BodyTextLarge", parent=self.styles["Normal"], fontSize=14, leading=20,
            textColor=self.dark_text, alignment=TA_JUSTIFY, spaceAfter=8, fontName="Helvetica"
        ))
        self.styles.add(ParagraphStyle(
            name="ImportantText", parent=self.styles["Normal"], fontSize=14, leading=20,
            textColor=self.primary_blue, alignment=TA_LEFT, spaceAfter=8, fontName="Helvetica-Bold"
        ))

    # ------------- Parsing / Nettoyage -------------
    def _clean_markdown(self, content: str) -> str:
        if not content:
            return ""
        text = content.replace("\r\n", "\n").replace("\r", "\n")
        # Placeholders fréquents et mots techniques indésirables
        text = re.sub(r"\[(?:[^\]]*(?:compl[eé]ter|completer|ins[eé]rer|à remplir)[^\]]*)\]", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\bNon spécifié\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\bmarkdown\b", "", text, flags=re.IGNORECASE)
        # Lignes système et doublons évidents
        cleaned: List[str] = []
        for ln in text.split("\n"):
            s = ln.strip()
            if s.lower().startswith("généré le ") or s.lower().startswith("page "):
                continue
            if s == "Rapport Psychiatrique":
                continue
            cleaned.append(ln)
        # Réduction des vides successifs
        out: List[str] = []
        last_empty = False
        for ln in cleaned:
            if ln.strip() == "":
                if not last_empty:
                    out.append("")
                last_empty = True
            else:
                out.append(ln)
                last_empty = False
        return "\n".join(out).strip()

    def _fmt_inline(self, text: str) -> str:
        try:
            text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
            text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
            text = re.sub(r"`(.*?)`", r"<font name='Courier'>\1</font>", text)
            return text
        except Exception:
            return text

    def _md_to_elements(self, md: str):
        elements = []
        if not md:
            return elements
        for raw in md.split("\n"):
            line = raw.strip()
            if not line:
                elements.append(Spacer(1, 6))
                continue
            # Titres (#, ##)
            if line.startswith("# "):
                elements.append(Paragraph(self._fmt_inline(line[2:]), self.styles["SectionHeader"]))
                continue
            if line.startswith("## "):
                elements.append(Paragraph(self._fmt_inline(line[3:]), self.styles["SectionHeader"]))
                continue
            # Puces (-, *)
            if line.startswith(('- ', '* ')):
                bullet = self._fmt_inline(line[2:])
                elements.append(Paragraph(f"• {bullet}", self.styles["BodyTextLarge"]))
                continue
            # Numérotées (1. ...)
            if re.match(r"^\d+\.\s+.+", line):
                num = re.sub(r"^(\d+)\.\s+", r"\1. ", line)
                elements.append(Paragraph(self._fmt_inline(num), self.styles["BodyTextLarge"]))
                continue
            # Paragraphe
            elements.append(Paragraph(self._fmt_inline(line), self.styles["BodyTextLarge"]))
        return elements

    # ---------------- Génération ----------------
    def generate_pdf(self, markdown_content: str, session_id: Optional[str] = None) -> Optional[str]:
        try:
            md = self._clean_markdown(markdown_content)

            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.close()

            doc = SimpleDocTemplate(
                tmp.name,
                pagesize=A4,
                rightMargin=40,
                leftMargin=40,
                topMargin=80,
                bottomMargin=60,
                title="Rapport Psychiatrique",
                author="PsyChat",
            )

            story = []

            # Titre, sous-titre
            story.append(Paragraph("RAPPORT PSYCHIATRIQUE", self.styles["ReportTitle"]))
            story.append(Paragraph("Synthèse clinique — générée par PsyChat", self.styles["ReportSubtitle"]))
            story.append(Spacer(1, 8))

            # Ligne d'accent visuelle
            story.append(self._accent_rule())
            story.append(Spacer(1, 6))

            # Section Bilan final
            story.append(Paragraph("Bilan final", self.styles["SectionHeader"]))

            # Corps du rapport (multi-pages autorisées pour lisibilité)
            elements = self._md_to_elements(md)
            story.extend(elements)

            # Bas de page (date + confidentiel)
            story.append(Spacer(1, 10))
            story.append(self._accent_rule(thin=True))
            date_str = datetime.now().strftime("Généré le %d/%m/%Y à %H:%M")
            story.append(Paragraph(f"<font size=9>{date_str} — Document confidentiel</font>", self.styles["BodyTextLarge"]))

            def _header_footer(canvas, doc_):
                canvas.setFillColor(self.primary_blue)
                canvas.rect(doc_.leftMargin, A4[1] - doc_.topMargin + 10, doc_.width, 2, stroke=0, fill=1)
                if self.logo_path and os.path.exists(self.logo_path):
                    try:
                        logo = ImageReader(self.logo_path)
                        canvas.drawImage(logo, A4[0] - doc_.rightMargin - 30, A4[1] - doc_.topMargin + 0, width=55, height=55, mask='auto')
                    except Exception:
                        pass

            doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
            return tmp.name
        except Exception as e:
            import traceback, logging
            logging.getLogger(__name__).error(f"Erreur PDF: {e}")
            traceback.print_exc()
            return None

    def _accent_rule(self, thin: bool = False):
        from reportlab.graphics.shapes import Drawing, Line
        d = Drawing(400, 2 if thin else 3)
        ln = Line(0, 1, 400, 1)
        ln.strokeColor = self.primary_blue
        ln.strokeWidth = 0.5 if thin else 1.2
        d.add(ln)
        return d


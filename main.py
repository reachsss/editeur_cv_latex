import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
from html import escape

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QTextCharFormat, QFont, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QTextEdit, QTextBrowser, QComboBox, QFileDialog,
    QMessageBox, QLabel, QSplitter, QInputDialog
)

STYLE_PROPERTY = 1001
ALIGN_PROPERTY = 1002

SYMBOLS = {
    "α": r"$\alpha$",
    "β": r"$\beta$",
    "γ": r"$\gamma$",
    "δ": r"$\delta$",
    "π": r"$\pi$",
    "λ": r"$\lambda$",
    "∞": r"$\infty$",
    "≤": r"$\leq$",
    "≥": r"$\geq$",
    "≠": r"$\neq$",
    "≈": r"$\approx$",
    "→": r"$\rightarrow$",
    "←": r"$\leftarrow$",
    "↔": r"$\leftrightarrow$",
    "√": r"$\sqrt{}$",
    "×": r"$\times$",
}


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(c, c) for c in text)


def alignment_latex(alignment):
    if alignment == Qt.AlignmentFlag.AlignCenter:
        return "center"
    if alignment == Qt.AlignmentFlag.AlignRight:
        return "flushright"
    return None


def fragment_to_latex(fragment) -> str:
    text = latex_escape(fragment.text())
    fmt = fragment.charFormat()

    if fmt.fontWeight() >= QFont.Weight.Bold:
        text = rf"\textbf{{{text}}}"
    if fmt.fontItalic():
        text = rf"\textit{{{text}}}"
    if fmt.fontUnderline():
        text = rf"\underline{{{text}}}"

    size = fmt.fontPointSize()
    if size and size > 0:
        text = (
            rf"{{\fontsize{{{size:.1f}pt}}{{{size * 1.2:.1f}pt}}"
            rf"\selectfont {text}}}"
        )
    return text


def document_to_latex(editor: QTextEdit) -> str:
    lines = []
    block = editor.document().begin()

    while block.isValid():
        parts = []
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid():
                parts.append(fragment_to_latex(frag))
            it += 1

        content = "".join(parts)
        style = block.blockFormat().property(STYLE_PROPERTY)
        align = block.blockFormat().alignment()

        if style == "title":
            content = rf"\section*{{{content}}}"
        elif style == "subtitle":
            content = rf"\subsection*{{{content}}}"

        env = alignment_latex(align)
        if env:
            content = rf"\begin{{{env}}}" + "\n" + content + "\n" + rf"\end{{{env}}}"

        lines.append(content)
        block = block.next()

    return "\n\n".join(lines)


def build_latex(body: str) -> str:
    return rf"""\documentclass[11pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage{{lmodern}}
\usepackage{{geometry}}
\usepackage{{hyperref}}
\usepackage{{amsmath,amssymb}}
\geometry{{margin=2cm}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{7pt}}

\begin{{document}}
{body}
\end{{document}}
"""


def html_fragment(fragment) -> str:
    text = escape(fragment.text()).replace("\n", "<br>")
    fmt = fragment.charFormat()

    size = fmt.fontPointSize()
    style = []
    if size and size > 0:
        style.append(f"font-size:{size:.1f}pt")
    if fmt.fontWeight() >= QFont.Weight.Bold:
        text = f"<strong>{text}</strong>"
    if fmt.fontItalic():
        text = f"<em>{text}</em>"
    if fmt.fontUnderline():
        text = f"<u>{text}</u>"

    if style:
        text = f"<span style=\"{' ;'.join(style)}\">{text}</span>"
    return text


def document_to_html(editor: QTextEdit) -> str:
    blocks = []
    block = editor.document().begin()

    while block.isValid():
        fragments = []
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid():
                fragments.append(html_fragment(frag))
            it += 1

        content = "".join(fragments) or "&nbsp;"
        style = block.blockFormat().property(STYLE_PROPERTY)
        align = block.blockFormat().alignment()

        css_align = "left"
        if align == Qt.AlignmentFlag.AlignCenter:
            css_align = "center"
        elif align == Qt.AlignmentFlag.AlignRight:
            css_align = "right"
        elif align == Qt.AlignmentFlag.AlignJustify:
            css_align = "justify"

        if style == "title":
            content = f"<h1>{content}</h1>"
        elif style == "subtitle":
            content = f"<h2>{content}</h2>"
        else:
            content = f"<p>{content}</p>"

        blocks.append(
            f'<div style="text-align:{css_align};">{content}</div>'
        )
        block = block.next()

    return f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{
    margin: 0;
    background: #d7d9dc;
    font-family: "Times New Roman", serif;
    color: #111;
}}
.page {{
    width: 794px;
    min-height: 1123px;
    box-sizing: border-box;
    margin: 22px auto;
    padding: 76px;
    background: white;
    box-shadow: 0 2px 12px rgba(0,0,0,.22);
    font-size: 11pt;
    line-height: 1.35;
}}
h1 {{
    font-size: 25pt;
    margin: 0 0 14px 0;
}}
h2 {{
    font-size: 16pt;
    margin: 16px 0 8px 0;
}}
p {{
    margin: 0 0 7px 0;
}}
</style>
</head>
<body>
<div class="page">
{''.join(blocks)}
</div>
</body>
</html>
"""


class CVEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Éditeur de CV LaTeX — V2")
        self.resize(1450, 900)

        self.editor = QTextEdit()
        self.editor.setAcceptRichText(True)
        self.editor.setPlaceholderText(
            "Écrivez votre CV ici…\n"
            "Vous n'avez pas besoin de connaître LaTeX."
        )
        self.editor.setFontPointSize(11)
        self.editor.textChanged.connect(self.schedule_preview)

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        self.preview.setStyleSheet("QTextBrowser { border: 0; }")

        self.build_toolbar()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.preview)
        splitter.setSizes([700, 700])
        self.setCentralWidget(splitter)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(180)
        self.timer.timeout.connect(self.update_preview)

        self.statusBar().showMessage(
            "Aperçu rapide actif — le PDF sera généré avec MiKTeX lors de l'export."
        )
        self.update_preview()

    def build_toolbar(self):
        toolbar = QToolBar("Mise en forme")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        def add_action(text, slot, shortcut=None):
            action = QAction(text, self)
            if shortcut:
                action.setShortcut(shortcut)
            action.triggered.connect(slot)
            toolbar.addAction(action)
            return action

        add_action("Gras", self.toggle_bold, QKeySequence.StandardKey.Bold)
        add_action("Italique", self.toggle_italic, QKeySequence.StandardKey.Italic)
        add_action("Souligné", self.toggle_underline, QKeySequence.StandardKey.Underline)

        toolbar.addSeparator()

        toolbar.addWidget(QLabel(" Taille : "))
        self.size_box = QComboBox()
        self.size_box.addItems(["9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32"])
        self.size_box.setCurrentText("11")
        self.size_box.currentTextChanged.connect(self.change_size)
        toolbar.addWidget(self.size_box)

        toolbar.addWidget(QLabel(" Style : "))
        self.style_box = QComboBox()
        self.style_box.addItems(["Texte", "Titre", "Sous-titre"])
        self.style_box.currentTextChanged.connect(self.change_style)
        toolbar.addWidget(self.style_box)

        toolbar.addSeparator()

        add_action("←", self.align_left)
        add_action("↔", self.align_center)
        add_action("→", self.align_right)
        add_action("☰", self.align_justify)

        toolbar.addSeparator()

        for symbol, latex in SYMBOLS.items():
            action = QAction(symbol, self)
            action.setToolTip(f"Insérer {symbol}")
            action.triggered.connect(
                lambda checked=False, s=symbol: self.insert_symbol(s)
            )
            toolbar.addAction(action)

        toolbar.addSeparator()

        add_action("Enregistrer", self.save_project, QKeySequence.StandardKey.Save)
        add_action("Ouvrir", self.open_project, QKeySequence.StandardKey.Open)
        add_action("Exporter .tex", self.export_tex)
        add_action("Exporter PDF", self.export_pdf)

    def current_cursor(self):
        return self.editor.textCursor()

    def merge_format(self, fmt):
        cursor = self.current_cursor()
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
            self.editor.setTextCursor(cursor)

    def toggle_bold(self):
        cursor = self.current_cursor()
        fmt = QTextCharFormat()
        current = cursor.charFormat().fontWeight()
        fmt.setFontWeight(
            QFont.Weight.Normal
            if current >= QFont.Weight.Bold
            else QFont.Weight.Bold
        )
        self.merge_format(fmt)

    def toggle_italic(self):
        cursor = self.current_cursor()
        fmt = QTextCharFormat()
        fmt.setFontItalic(not cursor.charFormat().fontItalic())
        self.merge_format(fmt)

    def toggle_underline(self):
        cursor = self.current_cursor()
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not cursor.charFormat().fontUnderline())
        self.merge_format(fmt)

    def change_size(self, value):
        if not value:
            return
        fmt = QTextCharFormat()
        fmt.setFontPointSize(float(value))
        self.merge_format(fmt)

    def change_style(self, value):
        cursor = self.current_cursor()
        block_fmt = cursor.blockFormat()
        block_fmt.setProperty(
            STYLE_PROPERTY,
            {"Texte": "text", "Titre": "title", "Sous-titre": "subtitle"}[value],
        )
        cursor.setBlockFormat(block_fmt)
        self.editor.setTextCursor(cursor)
        self.schedule_preview()

    def set_alignment(self, alignment):
        cursor = self.current_cursor()
        block_fmt = cursor.blockFormat()
        block_fmt.setAlignment(alignment)
        cursor.setBlockFormat(block_fmt)
        self.editor.setTextCursor(cursor)
        self.schedule_preview()

    def align_left(self):
        self.set_alignment(Qt.AlignmentFlag.AlignLeft)

    def align_center(self):
        self.set_alignment(Qt.AlignmentFlag.AlignCenter)

    def align_right(self):
        self.set_alignment(Qt.AlignmentFlag.AlignRight)

    def align_justify(self):
        self.set_alignment(Qt.AlignmentFlag.AlignJustify)

    def insert_symbol(self, symbol):
        self.editor.textCursor().insertText(symbol)
        self.schedule_preview()

    def schedule_preview(self):
        self.timer.start()

    def update_preview(self):
        self.preview.setHtml(document_to_html(self.editor))

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le projet", "mon_cv.html", "Projet CV (*.html)"
        )
        if not path:
            return
        Path(path).write_text(self.editor.toHtml(), encoding="utf-8")
        self.statusBar().showMessage(f"Projet enregistré : {path}")

    def open_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un projet", "", "Projet CV (*.html)"
        )
        if not path:
            return
        try:
            self.editor.setHtml(Path(path).read_text(encoding="utf-8"))
            self.update_preview()
            self.statusBar().showMessage(f"Projet ouvert : {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", str(exc))

    def export_tex(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter le fichier LaTeX", "cv.tex", "LaTeX (*.tex)"
        )
        if not path:
            return
        Path(path).write_text(
            build_latex(document_to_latex(self.editor)),
            encoding="utf-8"
        )
        self.statusBar().showMessage(f"LaTeX exporté : {path}")

    def export_pdf(self):
        compiler = shutil.which("pdflatex") or shutil.which("xelatex")
        if not compiler:
            QMessageBox.warning(
                self,
                "MiKTeX introuvable",
                "pdflatex/xelatex n'est pas trouvé dans le PATH de Windows.\n\n"
                "Fermez puis rouvrez l'application et vérifiez que MiKTeX est "
                "bien installé et que son dossier bin est dans le PATH."
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter le PDF", "cv.pdf", "PDF (*.pdf)"
        )
        if not path:
            return

        output = Path(path)
        with tempfile.TemporaryDirectory(prefix="latex_cv_") as tmp:
            workdir = Path(tmp)
            tex_path = workdir / "cv.tex"
            tex_path.write_text(
                build_latex(document_to_latex(self.editor)),
                encoding="utf-8"
            )

            try:
                result = subprocess.run(
                    [
                        compiler,
                        "-interaction=nonstopmode",
                        "-halt-on-error",
                        "-file-line-error",
                        "cv.tex",
                    ],
                    cwd=workdir,
                    capture_output=True,
                    text=True,
                    timeout=90,
                )
                pdf = workdir / "cv.pdf"

                if result.returncode != 0 or not pdf.exists():
                    details = (result.stdout or "") + "\n" + (result.stderr or "")
                    QMessageBox.critical(
                        self,
                        "Erreur de compilation LaTeX",
                        "MiKTeX a lancé la compilation, mais LaTeX a renvoyé une erreur.\n\n"
                        + details[-7000:]
                    )
                    return

                shutil.copy2(pdf, output)
                self.statusBar().showMessage(f"PDF exporté : {output}")
                QMessageBox.information(
                    self, "Export terminé", f"PDF créé avec succès :\n{output}"
                )

            except subprocess.TimeoutExpired:
                QMessageBox.critical(
                    self,
                    "Compilation trop longue",
                    "La compilation LaTeX a dépassé 90 secondes."
                )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CVEditor()
    window.show()
    sys.exit(app.exec())

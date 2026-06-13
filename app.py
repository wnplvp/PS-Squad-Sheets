#!/usr/bin/env python3
"""
Squad Sheet Generator — Streamlit web app
Parses a squadding HTML file and produces a printable PDF sign-in sheet.
"""

import streamlit as st
import re
import os
import subprocess
import shutil
import tempfile
from pathlib import Path

LOGO_NAME = 'LogoSmall.png'
ROWS = 15  # rows per squad page

# ── LaTeX template pieces (raw strings so backslashes are literal) ────────────

PREAMBLE = r"""\documentclass[letterpaper,12pt]{article}
\usepackage[top=0.7in,bottom=0.7in,left=0.9in,right=0.9in]{geometry}
\usepackage{graphicx}
\usepackage{array}
\usepackage{tabularx}
\usepackage{xcolor}
\usepackage{colortbl}
\usepackage{makecell}

\pagestyle{empty}
\setlength{\parindent}{0pt}

\begin{document}
"""

POSTAMBLE = r"""
\end{document}
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def find_pdflatex():
    """Find pdflatex on any platform."""
    found = shutil.which('pdflatex')
    if found:
        return found
    mac_path = '/Library/TeX/texbin/pdflatex'
    if os.path.isfile(mac_path):
        return mac_path
    return None


def escape_latex(text):
    for ch, repl in [('\\', r'\textbackslash{}'), ('&', r'\&'), ('%', r'\%'),
                     ('$', r'\$'), ('#', r'\#'), ('_', r'\_'),
                     ('{', r'\{'), ('}', r'\}')]:
        text = text.replace(ch, repl)
    return text


def _strip_tags(s):
    """Strip HTML tags and collapse whitespace."""
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def parse_html(content):
    """Return a list of (label, [shooter_string, ...]) tuples in document order.

    Strategy for the label, in priority order:
      1. A <strong>Squad N</strong> marker → use "Squad N".
      2. Any other <strong>...</strong> text in the cell → use that verbatim
         (covers things like "Unsquadded", "RO Squad", custom names, etc.).
      3. The first non-empty line of text in the cell → use that.
      4. Fallback to "Squad ?".

    Cells with zero numbered shooters are skipped entirely.
    """
    results = []
    fallback_idx = 0
    for td_match in re.finditer(r'<td[^>]*>(.*?)</td>', content, re.DOTALL):
        td = td_match.group(1)

        shooters = [
            m.group(1).strip()
            for m in re.finditer(r'\d+\.\s+(.+\))', td)
        ]
        if not shooters:
            continue

        # 1. Standard "Squad N" header
        sq = re.search(r'<strong>\s*Squad\s+(\d+)\s*</strong>', td)
        if sq:
            label = f'Squad {sq.group(1)}'
        else:
            # 2. Any other <strong>...</strong> text
            alt = re.search(r'<strong>(.*?)</strong>', td, re.DOTALL)
            label = _strip_tags(alt.group(1)) if alt else ''
            # 3. First non-empty line of plain text in the cell.
            # Split on <br>/block tags AND real newlines so the label doesn't
            # swallow the shooter rows that follow it.
            if not label:
                line_split = re.split(
                    r'<br\s*/?>|</?p>|</?div>|\r?\n',
                    td, flags=re.IGNORECASE,
                )
                for chunk in line_split:
                    chunk = _strip_tags(chunk)
                    # Skip lines that are just shooter entries (start with "N. ")
                    if chunk and not re.match(r'^\d+\.\s', chunk):
                        label = chunk
                        break
            # 4. Last-resort placeholder
            if not label:
                fallback_idx += 1
                label = f'Squad ? ({fallback_idx})'

        results.append((label, shooters))
    return results


def make_page(league_esc, squad_label, shooters, has_logo):
    """Build the LaTeX source for one squad page."""
    L = []

    # ── Header: league name + optional logo ──────────────────────────────────
    if has_logo:
        L += [
            r'\begin{minipage}[t]{0.62\textwidth}',
            r'  \vspace{0pt}',
            '  {\\Large\\textbf{' + league_esc + '}}',
            r'\end{minipage}%',
            r'\hfill',
            r'\begin{minipage}[t]{0.30\textwidth}',
            r'  \vspace{0pt}',
            r'  \raggedleft',
            '  \\includegraphics[width=2.3cm]{' + LOGO_NAME + '}',
            r'\end{minipage}',
        ]
    else:
        L.append('{\\Large\\textbf{' + league_esc + '}}')

    # ── Squad title ───────────────────────────────────────────────────────────
    label_esc = escape_latex(squad_label)
    L += [
        '',
        r'\vspace{0.6em}',
        '',
        r'\begin{center}',
        '  {\\fontsize{28}{32}\\selectfont\\textit{' + label_esc + '}}',
        r'\end{center}',
        '',
        r'\vspace{0.2em}',
        '',
    ]

    # ── Sign-in table ─────────────────────────────────────────────────────────
    L += [
        r'\renewcommand{\arraystretch}{1.0}',
        r'\begin{tabularx}{\textwidth}{|',
        r'    >{\centering\arraybackslash}p{0.7cm}|',
        r'    >{\centering\arraybackslash}p{1.5cm}|',
        r'    X|}',
        r'  \hline',
        r'  \rowcolor{black}',
        r'  \textcolor{white}{\small} &',
        r"  \textcolor{white}{\small\textbf{I'm Here}} &",
        r'  \textcolor{white}{\small\textbf{Shooter Name / Creds}} \\',
        r'  \hline',
    ]

    for i in range(1, ROWS + 1):
        name = escape_latex(shooters[i - 1]) if i <= len(shooters) else ''
        L.append(
            f'  \\raisebox{{-0.30cm}}{{\\small\\textbf{{{i}}}}} & ' +
            r'\hfil\raisebox{-0.45cm}{\framebox(18,18){}}\hfil & ' +
            f'\\raisebox{{-0.30cm}}{{{name}}} \\\\[1.0em]'
        )
        L.append(r'  \hline')

    L.append(r'\end{tabularx}')
    return '\n'.join(L)


def generate_latex(league_name, squads, has_logo):
    """squads is a list of (label, shooters) tuples in document order."""
    league_esc = escape_latex(league_name)
    pages = [
        make_page(league_esc, label, shooters, has_logo)
        for label, shooters in squads
    ]
    return PREAMBLE + '\n\\newpage\n'.join(pages) + POSTAMBLE


def compile_pdf(tex_path):
    pdflatex = find_pdflatex()
    if not pdflatex:
        return False, 'pdflatex not found on the server. Contact the administrator.'
    work_dir = os.path.dirname(tex_path)
    result = subprocess.run(
        [pdflatex, '-interaction=nonstopmode', os.path.basename(tex_path)],
        cwd=work_dir,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout + result.stderr


# ── Streamlit UI ──────────────────────────────────────────────────────────────

st.set_page_config(page_title='Squad Sheet Generator', page_icon='🎯', layout='centered')

st.title('Squad Sheet Generator')
st.write('Upload a squadding HTML file and generate a printable PDF sign-in sheet.')

with st.form('squad_form'):
    league_name = st.text_input('League Name', placeholder='e.g. Reno Practical Shooters')
    html_file = st.file_uploader('Squadding HTML File', type=['html', 'htm'])
    logo_file = st.file_uploader('Logo (optional, PNG)', type=['png'])
    submitted = st.form_submit_button('Generate PDF')

if submitted:
    if not league_name.strip():
        st.error('Please enter a league name.')
    elif not html_file:
        st.error('Please upload an HTML file.')
    else:
        with st.spinner('Generating PDF…'):
            try:
                # Decode HTML
                html_content = html_file.read().decode('utf-8', errors='replace')

                # Parse
                squads = parse_html(html_content)
                if not squads:
                    st.error('No squads found in the HTML file.')
                    st.stop()

                # Show parsed summary
                with st.expander('Parsed squads', expanded=True):
                    for label, shooters in squads:
                        st.write(f'**{label}:** {len(shooters)} shooter(s)')

                # Build everything in a temp dir so concurrent users don't collide
                with tempfile.TemporaryDirectory() as work_dir:
                    has_logo = False
                    if logo_file is not None:
                        logo_path = os.path.join(work_dir, LOGO_NAME)
                        with open(logo_path, 'wb') as f:
                            f.write(logo_file.read())
                        has_logo = True
                    else:
                        # Fall back to bundled logo if it exists alongside app.py
                        bundled_logo = Path(__file__).parent / LOGO_NAME
                        if bundled_logo.is_file():
                            shutil.copy2(bundled_logo, os.path.join(work_dir, LOGO_NAME))
                            has_logo = True

                    if not has_logo:
                        st.info('No logo provided — generating without logo.')

                    latex = generate_latex(league_name.strip(), squads, has_logo)
                    tex_path = os.path.join(work_dir, 'SquadSheets.tex')
                    pdf_path = os.path.join(work_dir, 'SquadSheets.pdf')

                    with open(tex_path, 'w', encoding='utf-8') as f:
                        f.write(latex)

                    ok, output = compile_pdf(tex_path)

                    if not ok:
                        st.error('PDF compilation failed.')
                        with st.expander('Compiler output'):
                            st.code(output[-2000:])
                        st.stop()

                    # Read the PDF for download
                    with open(pdf_path, 'rb') as f:
                        pdf_bytes = f.read()

                st.success('PDF generated successfully.')
                st.download_button(
                    label='Download SquadSheets.pdf',
                    data=pdf_bytes,
                    file_name='SquadSheets.pdf',
                    mime='application/pdf',
                )

            except Exception as exc:
                st.error(f'Error: {exc}')

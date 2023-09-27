from loguru import logger
from difflib import SequenceMatcher
from os.path import basename

import fitz
import wordninja
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def find_common_string(str1: str, str2: str) -> str:
    """
    Find the longest contiguous matching subsequence between two strings.

    Args:
        str1: The first input string.
        str2: The second input string.

    Returns:
        The common substring found in both input strings.
    """
    clean_str1 = str1.replace('\n', '').replace(' ', '').replace('.', '')
    clean_str2 = str2.replace('\n', '').replace(' ', '').replace('.', '')
    matcher = SequenceMatcher(None, clean_str1, clean_str2)
    match = matcher.find_longest_match(0, len(clean_str1), 0, len(clean_str2))
    common_string = clean_str1[match.a: match.a + match.size]
    return common_string


def find_start_end_index(page_text: str, extract_text: str) -> tuple[int, int]:
    words = extract_text.split()
    max_window_size = min(10, len(words))
    idx_start = next((page_text.find(' '.join(words[:max_window_size - i])) for i in range(max_window_size) if page_text.find(' '.join(words[:max_window_size - i])) > 0), None)
    idx_end = next((page_text.find(' '.join(words[i - max_window_size:]), idx_start) for i in range(max_window_size) if page_text.find(' '.join(words[i - max_window_size:]), idx_start) > 0), None)
    i_end = next((i for i in range(max_window_size) if page_text.find(' '.join(words[i - max_window_size:]), idx_start) > 0), None)

    return idx_start, idx_end + len(' '.join(words[i_end - max_window_size:])) if idx_end is not None else None


def get_document_page_data(doc: fitz.Document, text: str) -> tuple[int, str, str]:
    page_id = -1
    common_text = ''
    page_text = ''
    for i in range(len(doc)):
        extracted_page_text = doc[i].get_textpage().extractText()
        extracted_common_text = find_common_string(extracted_page_text, text)
        if len(extracted_common_text) > len(common_text):
            common_text = extracted_common_text
            page_id = i
            page_text = extracted_page_text
    return page_id, common_text, page_text


def highlight_file(file_name: str, text: str) -> str or None:
    """
    Highlight the specified text in the given file using PyMuPDF.

    Args:
        file_name: The file name to be modified with PyMuPDF.
        text: The text to be highlighted in the file.

    Returns:
        The name of the created temporary file with the highlighted text.
        None if the file is not found.
    """
    try:
        doc = fitz.open(file_name)
    except fitz.fitz.FileNotFoundError:
        logger.error(f'{file_name} is not found or cannot be opened by fitz')
        raise FileNotFoundError(f'{file_name} is not found')
    page_id, common_text, page_text = get_document_page_data(doc, text)
    splitten_text = " ".join(wordninja.split(common_text))
    idx_start, idx_end = find_start_end_index(page_text, splitten_text)
    to_highlight = page_text[idx_start:idx_end]
    text_instances = doc[page_id].get_textpage().search(to_highlight)
    for instance in text_instances:
        _ = doc[page_id].add_highlight_annot(instance)
    output_pdf = fitz.open()
    output_pdf.insert_pdf(doc, from_page=page_id, to_page=page_id)
    output_pdf.save(f'highlighted_page_{page_id}_{basename(file_name)}')
    doc.close()
    output_pdf.close()
    return f"highlighted_page_{page_id}_{basename(file_name)}"

def dict_to_pdf(dictionary: dict, report_title: str) -> None:
    """
    Generates a PDF report using the provided dictionary data.

    Args:
        dictionary (dict): A dictionary containing the report data.
            The keys represent the titles, and the values represent the content.
        report_title (str): The title of the generated report.

    Returns:
        None: The report is generated and saved as a PDF file.

    """
    # Create a list to hold the report elements
    report = []

    # Get the default sample style sheet
    styles = getSampleStyleSheet()

    # Create a custom style for the report title with increased font size
    title_style = ParagraphStyle(
        name="CustomTitleStyle",
        parent=styles["Title"],
        fontSize=24  # Adjust the font size as desired
    )

    # Create a title for the report with the custom style
    title = Paragraph("<b>Report</b>", title_style)
    report.append(title)
    report.append(Spacer(1, 8 * 5))

    # Iterate over dictionary items and add titles and content to the report
    for key, value in dictionary.items():
        title = Paragraph("<u><b>{}</b></u>".format(key), styles["Heading1"])
        content = Paragraph(value, styles["Normal"])
        report.append(title)
        report.append(Spacer(1, 8 * 5))  # Adjust the spacing as desired
        report.append(content)
        report.append(Spacer(1, 8 * 5))  # Adjust the spacing as desired

    # Create the PDF report
    doc = SimpleDocTemplate(report_title, pagesize=letter)
    doc.build(report)

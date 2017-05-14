from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine
import re


def get_issues_list(pdf_filename, pdf_type='Ansa'):
    """Pass."""
    fp = open(pdf_filename, 'rb')
    parser = PDFParser(fp)
    doc = PDFDocument()
    parser.set_document(doc)
    doc.set_parser(parser)
    doc.initialize('')
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    # Process each page contained in the document.
    matches = []
    for idx, page in enumerate(doc.get_pages(), 1):
        interpreter.process_page(page)
        layout = device.get_result()
        for lt_obj in layout:
            if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
                if pdf_type == 'Ansa':
                    if 'Incident:' in lt_obj.get_text():
                        match = re.findall(r'\[Incident:.*?\]', lt_obj.get_text())
                        if match:
                            matches.append(match[0])
                elif pdf_type == 'Meta':
                    if re.search(r'\d{5,}', lt_obj.get_text()):
                        matches.append(lt_obj.get_text())
    issues = []
    for inc in matches:
        match = re.findall(r'([\w-]+?\d+)', inc)
        [issues.append(each) for each in match]

    return issues

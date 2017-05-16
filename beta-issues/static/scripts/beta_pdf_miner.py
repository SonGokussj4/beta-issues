from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine
import re


def get_issues_list(pdf_filename: str, pdf_type: str = 'Ansa') -> set:
    """Returns set of tuples in format: {('issue-name', 'ANSA/META_version'), ..."""
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
    cur_ver = ''
    for idx, page in enumerate(doc.get_pages(), 1):
        interpreter.process_page(page)
        layout = device.get_result()
        for lt_obj in layout:
            if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
                # print('::[{}]::'.format(lt_obj.get_text()))
                if pdf_type == 'Ansa':
                    rel_match = re.findall(r'ANSA\Wv\d{2}[.]\d[.]\d(?=\W.*?Release Notes)', lt_obj.get_text())
                    if rel_match:
                        cur_ver = rel_match[0]
                    if 'Incident:' in lt_obj.get_text():
                        match = re.findall(r'\[Incident:.*?\]', lt_obj.get_text())
                        if match:
                            # print('ISSUES:', match[0], cur_ver)
                            matches.append({'issue': match[0], 'ver': cur_ver})
                elif pdf_type == 'Meta':
                    rel_match = re.findall(r'META\Wv\d{2}[.]\d[.]\d(?=\W.*?Release Notes)', lt_obj.get_text())
                    if rel_match:
                        cur_ver = rel_match[0]
                    if re.search(r'\d{5,}', lt_obj.get_text()):
                        # print('ISSUES:', lt_obj.get_text(), cur_ver)
                        matches.append({'issue': lt_obj.get_text(), 'ver': cur_ver})
    issues = set()
    for dc in matches:
        match = re.findall(r'([\w-]+?\d+)', dc.get('issue'))
        [issues.add((each, dc.get('ver'))) for each in match]

    return issues


# res = get_issues_list('D:\\Programovani\\github\\beta-issues\\TEST\\META_v17.1.1_Release_Notes.pdf', 'Meta')
# res = get_issues_list('D:\\Programovani\\github\\beta-issues\\TEST\\ansa_v17.0.x_release_notes.pdf', 'Ansa')
# print(res)

# def get_issues_list(pdf_filename, pdf_type='Ansa'):
#     """Pass."""
#     fp = open(pdf_filename, 'rb')
#     parser = PDFParser(fp)
#     doc = PDFDocument()
#     parser.set_document(doc)
#     doc.set_parser(parser)
#     doc.initialize('')
#     rsrcmgr = PDFResourceManager()
#     laparams = LAParams()
#     device = PDFPageAggregator(rsrcmgr, laparams=laparams)
#     interpreter = PDFPageInterpreter(rsrcmgr, device)

#     # Process each page contained in the document.
#     matches = []
#     for idx, page in enumerate(doc.get_pages(), 1):
#         interpreter.process_page(page)
#         layout = device.get_result()
#         for lt_obj in layout:
#             if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
#                 if pdf_type == 'Ansa':
#                     if 'Incident:' in lt_obj.get_text():
#                         match = re.findall(r'\[Incident:.*?\]', lt_obj.get_text())
#                         if match:
#                             matches.append(match[0])
#                 elif pdf_type == 'Meta':
#                     if re.search(r'\d{5,}', lt_obj.get_text()):
#                         matches.append(lt_obj.get_text())
#     issues = []
#     for inc in matches:
#         match = re.findall(r'([\w-]+?\d+)', inc)
#         [issues.append(each) for each in match]

#     return issues

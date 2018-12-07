from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine
import re


def _get_version(layout, pdf_type):
    """Scan the whole page and return BETA version."""
    cur_ver = ''
    for lt_obj in layout:
        if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):

            if pdf_type == 'Ansa':
                rel_match = re.findall(r'ANSA\Wv\d{2}[.]\d[.]\d(?=\W?.*?Release Notes)', lt_obj.get_text())
                if rel_match:
                    cur_ver = rel_match[0]
            elif pdf_type == 'Meta':
                rel_match = re.findall(r'[Mμ]ETA\Wv\d{2}[.]\d[.]\d(?=\W?.*?Release Notes)', lt_obj.get_text())
                if rel_match:
                    cur_ver = rel_match[0]
    return cur_ver


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
    for idx, page in enumerate(doc.get_pages(), 1):
        # if idx < 40:
        #     continue
        # if idx == 48:
        #     break
        interpreter.process_page(page)
        layout = device.get_result()
        cur_ver = _get_version(layout, pdf_type)
        # print("\n========\nPAGE: {}".format(idx))
        # print("Version: {}".format(cur_ver))

        for lt_obj in layout:
            if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
                # try:
                #     print('lt_obj### {}'.format(lt_obj))
                #     print('get_tx### {}'.format(lt_obj.get_text()))
                # except:
                #     pass
                if pdf_type == 'Ansa':
                    if 'Incident:' in lt_obj.get_text():
                        match = re.findall(r'\[Incident:.*?\]', lt_obj.get_text())
                        if match:
                            # print('ISSUES:', match[0], cur_ver)
                            matches.append({'issue': match[0], 'ver': cur_ver})
                elif pdf_type == 'Meta':
                    if re.search(r'\d{5,6}(?![\.\d])', lt_obj.get_text()):
                        # print('ISSUES:', lt_obj.get_text(), cur_ver)
                        # print('lt_obj### {}'.format(lt_obj))
                        # print('get_tx### {}'.format(lt_obj.get_text()))
                        if '[' and ']' in lt_obj.get_text() or len(lt_obj.get_text()) < 55:
                            matches.append({'issue': lt_obj.get_text(), 'ver': cur_ver})
    issues = set()
    for dc in matches:
        match = re.findall(r'([\w-]+?\d+)', dc.get('issue'))
        [issues.add((each, dc.get('ver'))) for each in match]

    return issues

# res = get_issues_list('META_Release_Notes_v16.x.x.pdf', 'Meta')
# for each in res:
#     print(each)
# print(len(res))

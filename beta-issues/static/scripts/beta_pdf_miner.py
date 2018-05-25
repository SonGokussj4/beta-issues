"""PDF Miner of ANSA and META release notes.

> ANSA release notes:
ANSA v18.0.1 Release Notes
ANSA v18.0.0 Release Notes
ANSA v17.1.0 Release Notes
ANSA v17.0.0 Release Notes
ANSA v16.2.1 Release Notes
ANSA v15.3.0 Release Notes

> ANSA types:
[ANSA-12345]  # without Incident
[Incident: ANSA-12345]  # only one
[Incident: ANSA-12345, ANSA-54321]  # more than one
[Incident: 12345, ANSA-54321]  # without "ANSA-"
[Incidents: ANSA-27072, ANSA-31651, ANSA-58347]  # multiple number of incidentS
[Incidents: ANSA-27072,
    ANSA-31651, ANSA-58347]  # multiple rows
[incident: ANSA-62744]  # small i on the beginning
text before [62744]  # text before - THIS NOT
[62744]  # only a number without anything else
[Incident: ANSA-42178  # without right square bracket
[Incident: ANSA 59111]  # without dash
[Incident: ANSA21525]  # without space
[Incident: ANSA-59549, ANSA - 56711]  # spaces next around dash
[Incident: ANSA:53651, ANSA: 53656, ANSA-54004]  # column istead of dash with optional space
[Incident: NSA-59992]  # not ANSA but NSA
[Incident: ansa-62343]  # ansa with small case
[Incident: 53061/ ANSA-33604, 63283/ANSA-39800, ANSA-33775]  # don't know
[Incident: 54485/ANSA-34584, 59936/ANSA-38452,
    64739/ANSA-41926, 58977 /ANSA-37784]  # don't know what format (number/ansa-number?) and multi line
[Incident: 57343, ANSA_36671]  # understroke instead of dash or space or column or nothing

> META release notes:
META v18.1.0 Release Notes
META v17.1.3 Release Notes
META v17.1.0 Release Notes
META v16.2.4 Release Notes
μETA v17.0.2 Release Notes
μETA v17.0.1 Release Notes
μETA v16.2.0 Release Notes

> META types:
META-20719
# 20230, #58749, #64979, META-17823, META-21465
39340, META-13126
#32570, META-11059
# 26911, META-21360
META-13126, 39340
[Incident: META-22258]
[Incident: 27726, 42570]
[Incident: 40480, 51742, META-19869]
[3362, 27411, 59601, META-1143, META-9745, META-18046
[280, META-75
[1523, META-510
"""

from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine
import re

# REGEX
# regex_ansa = re.compile(r'^\s*[\[,](?:Incident[s]?)?.*(?:[A]?NSA[ -])?\d{4,}\]?', flags=re.IGNORECASE | re.MULTILINE)
regex_ansa = re.compile(
    r'^\s*(?:[\[,]|\d{4,})(?:Incident[s]?)?.*(?:[A]?NSA)?\d{4,}\]?',
    flags=re.IGNORECASE | re.MULTILINE)
regex_meta = re.compile(
    # r'((?:[#][ ]?)?(?:(?:ANSA|META)[- ])?\d{4,7})[^.]',
    r'(?:[#][ ]?)?(?:(?:ANSA|META)[- ])?\d{4,7}(?!\.)',
    flags=re.IGNORECASE | re.MULTILINE)


def _get_version(layout, pdf_type):
    """Scan the whole page and return BETA version."""
    cur_ver = ''
    for lt_obj in layout:
        if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):

            if pdf_type == 'Ansa':
                rel_match = re.findall(r'ANSA\Wv\d{2}[.]\d[.]\d(?=\W?.*?Release Notes)', lt_obj.get_text(),
                                       flags=re.IGNORECASE)
                if rel_match:
                    cur_ver = rel_match[0].capitalize()

            elif pdf_type == 'Meta':
                rel_match = re.findall(r'[Mμ]ETA\Wv\d{2}[.]\d[.]\d(?=\W?.*?Release Notes)', lt_obj.get_text(),
                                       flags=re.IGNORECASE)
                if rel_match:
                    cur_ver = rel_match[0].replace('μ', 'M').capitalize()
    return cur_ver


# def get_issues_list(pdf_filename: str, pdf_type: str = 'Ansa') -> set:
def get_issues_list(pdf_filename: str) -> set:
    """Returns set of tuples in format: {('issue-name', 'ANSA/META_version'), ..."""
    fp = open(pdf_filename, mode='rb')
    parser = PDFParser(fp)
    doc = PDFDocument()
    parser.set_document(doc)
    doc.set_parser(parser)
    doc.initialize('')
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    pdf_type = 'Ansa' if 'ansa' in pdf_filename.lower() else 'Meta'
    # print("DEBUG: pdf_type:", pdf_type)

    # Process each page contained in the document.
    all_matches = []
    for page_num, page in enumerate(doc.get_pages(), 1):
        # if page_num < 40:
        #     continue
        # if page_num == 48:
        #     break
        interpreter.process_page(page)
        layout = device.get_result()
        cur_ver = _get_version(layout, pdf_type)
        # print("\n========\nPAGE: {}".format(page_num))
        # print("Version: {}".format(cur_ver))

        for lt_obj in layout:
            if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
                # Strip text from lt_obj from right and replace new_lines for spaces
                get_tx_stripped = lt_obj.get_text().strip()
                # try:
                #     # print('\nlt_obj### {}'.format(lt_obj))
                #     print('get_tx### {}'.format(get_tx_stripped))
                # except Exception as e:
                #     print("lt_obj and get_tx EXCEPTION error")
                #     # pass
                if pdf_type == 'Ansa':
                    matches = regex_ansa.findall(get_tx_stripped)
                    if matches:
                        # print("MATCHES: {}".format(matches))
                        for match in matches:
                            if not match.endswith(']'):
                                match = '{match}]'.format(match=match)
                            # print('ISSUES:', match, cur_ver)
                            all_matches.append({'issue': match, 'ver': cur_ver, 'page_num': page_num})
                elif pdf_type == 'Meta':
                    matches = regex_meta.findall(get_tx_stripped)
                    if matches and (get_tx_stripped.lower().startswith(
                            ('[', '#', 'incident', 'meta', 'ansa')) or get_tx_stripped[0].isdigit()):
                        # print("MATCHES: {}".format(matches))
                        for match in matches:
                            match = '[{}]'.format(match.replace(']', ''))
                            # print('ISSUES:', match, cur_ver)
                            all_matches.append({'issue': match, 'ver': cur_ver, 'page_num': page_num})
    issues = set()
    reg_both = re.compile(r'(?:(?:(?:[A]?NSA)|(?:META))[ ]?[-:_#]?[ ]?)?(?:# |#)?\d{4,}', re.IGNORECASE)
    for dc in all_matches:
        match = reg_both.findall(dc.get('issue'))
        [issues.add((each, dc.get('ver'), dc.get('page_num'))) for each in match]

    return issues


# filepath = 'ANSA_release_notes_v1810.pdf'  # 530 1 META-27540
# filepath = 'ansa_release_notes_v1801.pdf'  # 898
# filepath = 'ansa_release_notes_v1713.pdf'  # 1103
# filepath = 'ansa_release_notes_v1710.pdf'  # 629
# filepath = 'ansa_release_notes_v1702.pdf'  # !!! NEJDE !!!
# filepath = 'ansa_release_notes_v1701.pdf'  # 762
# filepath = 'ansa_release_notes_v1700.pdf'  # 463
# filepath = 'ansa_release_notes_v1624.pdf'  # 675
# filepath = 'ansa_release_notes_v1621.pdf'  # 563
# filepath = 'ansa_release_notes_v1531.pdf'  # 95
# filepath = 'ansa_v17.0.x_release_notes_v1710.pdf'  # 1074
# filepath = 'ansa_v16.x.x_release_notes_v1703.pdf'  # 675 1 META-22427
# filepath = 'ansa_v16.x.x_release_notes_v1702.pdf'  # 563

# filepath = 'META_Release_Notes_v1810.pdf'  # 440
# filepath = 'META_Release_Notes_v1801.pdf'  # 401
# filepath = 'META_Release_Notes_v1713.pdf'  # 628
# filepath = 'META_Release_Notes_v1710.pdf'  # 346
# filepath = 'META_Release_Notes_v16.x.x_v1710.pdf'  # 1259
# filepath = 'META_Post_Release_Notes_v1704.pdf'  # 478 | 471

# filepath = 'META_Post_Release_Notes_v1702.pdf'  # 402 | 395
# filepath = 'META_Post_Release_Notes_v1700.pdf'  # 237 | 232
# filepath = 'META_Post_Release_Notes_v1624.pdf'  # 402 | 396
# filepath = 'META_Post_Release_Notes_v1621.pdf'  # 240 | 236
# filepath = 'META_Post_v16.x.x_Release_Notes_v1704.pdf'  # 1270 | 1260
# filepath = 'META_Post_v15.x.x_Release_Notes_v1700.pdf'  # 1264 | 1256
# filepath = 'META_Post_v15.3.1_Release_Notes_v1531.pdf'  # 35


# vertype = 'Ansa'
# vertype = 'Meta'

# res = get_issues_list(filepath, vertype)
# res = get_issues_list(filepath)

# for each in res:
#     print(each)
# print(len(res))

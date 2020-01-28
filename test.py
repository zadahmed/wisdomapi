import pdfplumber
pdf = pdfplumber.open('statements.pdf')
page = pdf.pages[0]
text = page.extract_text()
print(text)
pdf.close()
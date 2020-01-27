from tika import parser
import tika


url = 'https://www.whitehouse.gov/wp-content/uploads/2017/12/NSS-Final-12-18-2017-0905.pdf'

pdfFile = parser.from_file(url)

print(pdfFile["content"])
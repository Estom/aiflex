#!/usr/bin/env python3

import sys
import os

try:
    import pdfplumber
except ImportError:
    print("pdfplumber not installed. Installing...")
    os.system("pip install pdfplumber")
    import pdfplumber

def read_pdf(pdf_path, max_pages=5):
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        for i in range(min(max_pages, len(pdf.pages))):
            print(f"\n--- Page {i+1} ---")
            text = pdf.pages[i].extract_text()
            if text:
                print(text[:1000])  # First 1000 characters
            else:
                print("(No extractable text)")

if __name__ == "__main__":
    pdf_path = "/home/estom/work/pstock/examples/workspace/economy.pdf"
    read_pdf(pdf_path)
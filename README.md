# PDFShitBox

A lightweight PDF viewer and editor built with PyQt5 and PyMuPDF.

The interface now uses a modern dark theme and supports multiple actor
profiles (e.g. businesses, governments, gyms) so that annotations can be
attributed to different entities.

## Features
- View PDF documents page by page.
- Draw lines, rectangles, ellipses, and text boxes on pages.
- Color‑coded annotations per actor profile.
- Add and switch between different actors such as Businesses, Governments
  and Gyms.
- Save annotated PDFs.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python pdf_editor.py
```
Use the toolbar to open a PDF, navigate pages, draw shapes, manage actors,
and save your changes.

### Logging

Running the application creates a `pdf_editor.log` file in the working directory.
The log contains detailed information about actions taken and any errors
encountered, which can help diagnose issues such as problems displaying a PDF.

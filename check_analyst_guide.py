from pypdf import PdfReader

path = "docs/analyst_guide.pdf"

reader = PdfReader(path)

text = "\n".join(
    page.extract_text() or ""
    for page in reader.pages
).lower()

checks = {
    "Streamlit screener": (
        "streamlit" in text and
        "screener" in text
    ),

    "Dashboard navigation": (
        "dashboard" in text and
        (
            "navigate" in text or
            "navigation" in text
        )
    ),

    "PDF tearsheets": (
        "tearsheet" in text or
        "tear sheet" in text
    ),

    "API examples": (
        "curl" in text and
        "api" in text
    ),

    "Troubleshooting": (
        "troubleshoot" in text or
        "troubleshooting" in text
    ),
}

print("=" * 70)
print(f"PDF pages: {len(reader.pages)}")
print("=" * 70)

for name, passed in checks.items():
    print(f"{name}: {'PASS' if passed else 'MISSING'}")

print("=" * 70)

if len(reader.pages) >= 10 and all(checks.values()):
    print("ANALYST GUIDE CHECK: PASS")
else:
    print("ANALYST GUIDE CHECK: FAIL")

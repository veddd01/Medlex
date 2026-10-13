# data/

Place your medical encyclopedia PDF here as:

```
data/medical_book.pdf
```

That's the path `ingest.py` and `src/config.py` default to. Use `--pdf-path`
to point at a different file or location instead, e.g.:

```bash
python ingest.py --pdf-path /path/to/your/encyclopedia.pdf
```

## Sample PDF

`sample_medical_book.pdf` is a small, 9-page placeholder included so you can
smoke-test the ingestion pipeline immediately, without waiting to source a
real 700+ page encyclopedia first:

```bash
python ingest.py --pdf-path data/sample_medical_book.pdf --index-name medlex-sample
python app.py
```

Its content was written from scratch for this project (a handful of general,
well-established public-health topics) — it is **not** sourced from any real
encyclopedia, is not comprehensive, and is not a substitute for one. Swap in
your real reference PDF before using this for anything beyond testing.

(Regenerate it any time with `python scripts/_generate_sample_pdf.py`, which
requires `reportlab` — `pip install reportlab`.)

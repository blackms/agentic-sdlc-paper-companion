PAPER = main
PUB = rocchi-2026-measuring-llm-agents
LATEX = pdflatex
BIBTEX = bibtex
LATEX_OPTS = -interaction=nonstopmode -halt-on-error

.PHONY: all clean distclean tectonic arxiv-package

all: $(PUB).pdf

# arxiv-package: refresh the arXiv submission directory + tarball from the
# current source tree. Run after a clean `make` so the published PDF is current.
ARXIV_DIR = ../v1.4/arxiv-package
ARXIV_TAR = ../v1.4/arxiv-package.tar.gz
arxiv-package: $(PUB).pdf
	mkdir -p $(ARXIV_DIR)
	cp *.tex references.bib Makefile $(PUB).pdf $(ARXIV_DIR)/
	tar czf $(ARXIV_TAR) -C ../v1.4 arxiv-package
	@echo "arXiv tarball -> $(ARXIV_TAR)"

$(PUB).pdf: $(wildcard *.tex) references.bib
	$(LATEX) $(LATEX_OPTS) $(PAPER).tex
	$(BIBTEX) $(PAPER) || true
	$(LATEX) $(LATEX_OPTS) $(PAPER).tex
	$(LATEX) $(LATEX_OPTS) $(PAPER).tex
	mv $(PAPER).pdf $(PUB).pdf

# Alternative: use tectonic (single-pass, automatic deps)
tectonic:
	tectonic $(PAPER).tex
	mv $(PAPER).pdf $(PUB).pdf

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.toc *.lof *.lot *.fls *.fdb_latexmk *.synctex.gz $(PAPER).pdf

distclean: clean
	rm -f $(PUB).pdf

#%.png : %.dia
#	dia --export=$*.png $<

%.png : %.eps
	cat $< | \
	pstopnm -llx -10 -lly -10 -urx 10 -ury 10 \
		-nocrop -xborder 0 -yborder 0 -portrait \
		-xmax 3600 -ymax 3600 -verbose -stdout | \
	pnmcrop | pnmtopng -verbose > $*.png

%.eps : %.dia
	dia --export=$*.eps $<

%.pdf : %.eps
	epstopdf $<



DIAFIGS = \
	uc_tailor.dia uc_maint.dia uc_softdev.dia uc_kit.dia \
	pkg_qmconfig.dia pkg_bdist.dia pkg_boot.dia \
		pkg_build.dia pkg_lang.dia \
	cl_pdd.dia cl_probe.dia cl_tailor.dia cl_tailorsym.dia

PNGFIGS = $(DIAFIGS:.dia=.png)

EPSFIGS = $(DIAFIGS:.dia=.eps)

PDFFIGS = $(DIAFIGS:.dia=.pdf)

all: $(PNGFIGS) $(EPSFIGS) $(PDFFIGS)

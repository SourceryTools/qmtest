%.png : %.dia
	dia --export=$*.png $<

IMAGES =  \
	uc_kit.png uc_maint.png uc_softdev.png uc_tailor.png \
	pkg_bdist.png pkg_boot.png pkg_build.png pkg_lang.png pkg_sapcat.png \
	cl_pdd.png cl_probe.png cl_tailor.png

TIDY = tidy -numeric -indent 

all: sapcat_final.htm $(IMAGES)

install : sapcat_final.htm $(IMAGES)
	-rm -rf SapCat.OLD
	-mv SapCat SapCat.OLD
	mkdir SapCat
	cp sapcat_final.htm SapCat/index.html
	cp $(IMAGES) SapCat

sapcat_final.htm: \
    sapcat_final.xml sapcat.css sapcat_abbrevs \
    sapcat_intro.xml \
    sapcat_req.xml \
    sapcat_over.xml \
    sapcat_design.xml \
    sapcat_devplan.xml \
    sapcat_app_ideas.xml
	rm -f out.htm sapcat_final.htm
	doccvt/doccvt.py sapcat_final.xml
	$(TIDY) -n out.htm > sapcat_final.htm

sapcat_intro.htm: sapcat_intro.xml sapcat.css sapcat_abbrevs
	rm -f out.htm sapcat_intro.htm
	doccvt/doccvt.py sapcat_intro.xml
	$(TIDY) -n out.htm > sapcat_intro.htm

sapcat_req.htm: sapcat_req.xml sapcat.css sapcat_abbrevs
	rm -f out.htm sapcat_req.htm
	doccvt/doccvt.py sapcat_req.xml
	$(TIDY) -n out.htm > sapcat_req.htm

sapcat_over.htm: sapcat_over.xml sapcat.css sapcat_abbrevs
	rm -f out.htm sapcat_over.htm
	doccvt/doccvt.py sapcat_over.xml
	$(TIDY) -n out.htm > sapcat_over.htm

sapcat_design.htm: sapcat_design.xml sapcat.css sapcat_abbrevs
	rm -f out.htm sapcat_design.htm
	doccvt/doccvt.py sapcat_design.xml
	$(TIDY) -n out.htm > sapcat_design.htm

realclean: clean
	rm -rf SapCat

clean:
	rm -rf SapCat.OLD
	rm -f sapcat_final.htm
	rm -f sapcat_intro.htm
	rm -f sapcat_req.htm
	rm -f sapcat_over.htm
	rm -f sapcat_design.htm
	rm -f out.htm
	rm -f *~

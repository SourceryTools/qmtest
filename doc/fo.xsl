<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                version='1.0'>

<xsl:import 
 href="http://docbook.sourceforge.net/release/xsl/current/fo/docbook.xsl"/> 

<xsl:param name="csl_docbook.root" select="'.'"/>

<!--
  Fonts
-->
<xsl:attribute-set name="monospace.properties">
  <xsl:attribute name="font-size">8pt</xsl:attribute>
</xsl:attribute-set>
<xsl:attribute-set name="section.title.level1.properties">
  <xsl:attribute name="font-size">18pt</xsl:attribute>
</xsl:attribute-set>
<xsl:attribute-set name="section.title.level2.properties">
  <xsl:attribute name="font-size">12pt</xsl:attribute>
</xsl:attribute-set>
<xsl:attribute-set name="section.title.level3.properties">
  <xsl:attribute name="font-size">10pt</xsl:attribute>
</xsl:attribute-set>

<!--
  Page Layout
-->

<xsl:param name="page.margin.inner">1.5in</xsl:param>
<xsl:param name="page.margin.outer">1.5in</xsl:param>

<!-- Custom page layouts.  -->
<xsl:template name="user.pagemasters">

 <!-- Like the default 'titlepage' layout, except that the top-margin for
      the first page is increased.  -->
 <fo:page-sequence-master master-name="csl-titlepage">
   <fo:repeatable-page-master-alternatives>
     <fo:conditional-page-master-reference master-reference="blank"
					   blank-or-not-blank="blank"/>
     <fo:conditional-page-master-reference master-reference="csl-body-first"
					   page-position="first"/>
     <fo:conditional-page-master-reference master-reference="titlepage-odd"
					   odd-or-even="odd"/>
     <fo:conditional-page-master-reference 
					   odd-or-even="even">
       <xsl:attribute name="master-reference">
	 <xsl:choose>
	   <xsl:when test="$double.sided != 0">titlepage-even</xsl:when>
	   <xsl:otherwise>titlepage-odd</xsl:otherwise>
	 </xsl:choose>
       </xsl:attribute>
     </fo:conditional-page-master-reference>
   </fo:repeatable-page-master-alternatives>
 </fo:page-sequence-master>

 <!-- Like the default 'body' layout, except that the top-margin for
      the first page is increased.  -->
 <fo:page-sequence-master master-name="csl-body">
   <fo:repeatable-page-master-alternatives>
     <fo:conditional-page-master-reference master-reference="blank"
					   blank-or-not-blank="blank"/>
     <fo:conditional-page-master-reference master-reference="csl-body-first"
					   page-position="first"/>
     <fo:conditional-page-master-reference master-reference="body-odd"
					   odd-or-even="odd"/>
     <fo:conditional-page-master-reference 
					   odd-or-even="even">
       <xsl:attribute name="master-reference">
	 <xsl:choose>
	   <xsl:when test="$double.sided != 0">body-even</xsl:when>
	   <xsl:otherwise>body-odd</xsl:otherwise>
	 </xsl:choose>
       </xsl:attribute>
     </fo:conditional-page-master-reference>
   </fo:repeatable-page-master-alternatives>
 </fo:page-sequence-master>

 <fo:simple-page-master master-name="csl-body-first"
			page-width="{$page.width}"
			page-height="{$page.height}"
			margin-top="{$page.margin.top}"
			margin-bottom="{$page.margin.bottom}"
			margin-left="{$margin.left.inner}"
			margin-right="{$page.margin.outer}">
   <fo:region-body margin-bottom="{$body.margin.bottom}"
		   margin-top="33%"
		   column-gap="{$column.gap.body}"
		   column-count="{$column.count.body}">
   </fo:region-body>
   <fo:region-before region-name="xsl-region-before-first"
		     extent="{$region.before.extent}"
		     display-align="before"/>
   <fo:region-after region-name="xsl-region-after-first"
		    extent="{$region.after.extent}"
		    display-align="after"/>
 </fo:simple-page-master>
</xsl:template>

<xsl:template name="select.user.pagemaster">
 <xsl:param name="element"/>
 <xsl:param name="pageclass"/>
 <xsl:param name="default-pagemaster"/>

 <xsl:choose>
  <xsl:when test="$default-pagemaster = 'titlepage'">
   <xsl:value-of select="'csl-titlepage'"/>
  </xsl:when>
  <xsl:when test="$default-pagemaster = 'body' 
                  or $default-pagemaster='front'">
   <xsl:value-of select="'csl-body'"/>
  </xsl:when>
  <xsl:otherwise>
   <xsl:value-of select="$default-pagemaster"/>
  </xsl:otherwise>
 </xsl:choose>
</xsl:template>

<!--
  Style
-->

<xsl:param name="section.autolabel">1</xsl:param>
<xsl:param name="section.label.includes.component.label">1</xsl:param>
<xsl:param name="shade.verbatim">1</xsl:param>

<!-- Show URLs as footnotes since inserting them inline makes it hard to 
     break lines.  -->
<xsl:param name="ulink.footnotes">1</xsl:param>

<!-- Format these items like code.  -->
<xsl:template match="guibutton|guimenu|guisubmenu|guimenuitem">
 <xsl:call-template name="inline.monoseq"/>
</xsl:template>

<!-- Use hanging indents for titles; the body text starts 0.5in in from 
     the titles.  -->
<xsl:param name="body.start.indent">0.5in</xsl:param>
<xsl:attribute-set name="abstract.properties">
  <xsl:attribute name="start-indent">0.5in</xsl:attribute>
</xsl:attribute-set>
<xsl:template match="section|sect1|sect2|sect3|sect4|sect5"
              mode="object.title.markup">
  <fo:list-block provisional-label-separation="0.2em"
                 provisional-distance-between-starts="0.5in"
                 margin-left="0.0in"
                 xsl:use-attribute-sets="section.title.properties"
                 >
    <fo:list-item>
      <fo:list-item-label end-indent="label-end()" text-align="start">
        <fo:block>
          <xsl:apply-templates select="." mode="label.markup"/>
        </fo:block>
      </fo:list-item-label>
      <fo:list-item-body start-indent="body-start()">
        <fo:block>
          <xsl:apply-templates select="." mode="title.markup"/>
        </fo:block>
      </fo:list-item-body>
    </fo:list-item>
  </fo:list-block>
</xsl:template>

<!-- Format chapter titles on two lines.  -->
<xsl:template match="chapter" mode="object.title.markup">
 <fo:block>
  <xsl:text>Chapter </xsl:text>
  <xsl:apply-templates select="." mode="label.markup"/>
 </fo:block>
 <fo:block>
  <xsl:apply-templates select="." mode="title.markup"/>
 </fo:block>
</xsl:template>

<!-- We are never in draft mode. -->
<xsl:param name="draft.mode">no</xsl:param>

<!--
  Titlepage
-->

<xsl:template match="corpauthor" mode="book.titlepage.recto.mode">
 <fo:block-container absolute-position="absolute" top="3in">
  <fo:block>
   <fo:external-graphic src="url({$csl_docbook.root}/graphics/csl-logo.pdf)" />
  </fo:block>
 </fo:block-container>
</xsl:template>

<xsl:template name="chapter.titlepage.separator">
 <fo:block break-before="page"/>
</xsl:template>

<xsl:template name="preface.titlepage.separator">
 <fo:block break-before="page"/>
</xsl:template>

<xsl:template name="formal.object.heading" match="abstract" />

</xsl:stylesheet>

<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
                xmlns:common="http://exslt.org/common"
                xmlns:date="http://exslt.org/dates-and-times" 
                xmlns:func="http://exslt.org/functions" 
                xmlns:str="http://exslt.org/strings" 
                extension-element-prefixes="common date func str" version="1.0">

<!-- 

  File:   report.xslt
  Author: Stefan Seefeld
  Date:   2005-02-13

  Contents:
    templates for xhtml report generation

  Copyright (c) 2005 by CodeSourcery, LLC.  All rights reserved. 

-->

  <xsl:output omit-xml-declaration="no" indent="yes" encoding="UTF-8" method="xml" />       
    
  <!-- Customizable section

  Override the following parameters and templates to adjust the style of the
  html that is being generated.

  -->


  <!-- Define the title of the main page -->
  <xsl:param name="title" select="''" />

  <!-- 'key' is used to identify results (result files) -->
  <xsl:param name="key" select="'qmtest.run.end_time'" />

  <!-- Result annotations not to include in the report -->
  <xsl:param name="excluded.annotations" select="''" />

  <!-- Generate the main report page -->
  <xsl:template name="report.page">
    <html>
      <head>
        <title><xsl:value-of select="$title" /></title>
      </head>
      <body>
        <h1><xsl:value-of select="$title" /></h1>
        <!-- summary -->
        <div class="summary">
          <p class="heading">Summary</p>
          <xsl:call-template name="summary" />
        </div>
        <!-- generate result matrix -->
        <xsl:call-template name="matrix" />
        <!-- generate detailed pages, one per result set. -->
        <xsl:call-template name="details" />
      </body>
    </html>
  </xsl:template>

  <xsl:template name="detail.page">
    <xsl:param name="id" select="'dummy'"/>
    <!-- FIXME: Make sure the 'id' parameter is actually usable as a filename on the target OS. -->
    <xsl:variable name="filename">
      <xsl:call-template name="detail.document.name">
        <xsl:with-param name="name" select="$id" />
      </xsl:call-template>
    </xsl:variable>
    <common:document href="{$filename}" method="xml" indent="yes" encoding="ISO-8859-1">
      <xsl:variable name="title">
        Detailed results for test suite <xsl:value-of select="$id" />        
      </xsl:variable>
      <html>
        <head>
          <title><xsl:value-of select="$title" /></title>
        </head>
        <body>
          <h1><xsl:value-of select="$title" /></h1>
          <xsl:call-template name="detail" />
        </body>
      </html>
    </common:document>
  </xsl:template>

  <!-- QMTest report generation templates.

       These templates shouldn't be required to be redefined
   -->

  <xsl:template match="report">
    <xsl:call-template name="report.page" />
  </xsl:template>

  <xsl:template name="summary">
    <p><xsl:value-of select="count(/report/results/result)"/> tests</p>
    <p><xsl:value-of select="count(/report/results/result[@outcome='PASS'])"/> passes</p>
    <p><xsl:value-of select="count(/report/results/result[@outcome='FAIL'])"/> failures</p>
  </xsl:template>

  <xsl:template name="matrix">
    <table>
      <tbody>
        <th></th>
        <xsl:for-each select="/report/results">
          <th><xsl:value-of select="annotation[@key=$key]"/></th>
        </xsl:for-each>
        <xsl:for-each select="/report/suite/test/@id">
          <xsl:call-template name="matrix.row">
            <xsl:with-param name="id" select="." />
          </xsl:call-template>
        </xsl:for-each>
      </tbody>
    </table>
  </xsl:template>

  <xsl:template name="details">
    <xsl:for-each select="/report/results">
      <xsl:call-template name="detail.page">
        <xsl:with-param name="id" select="annotation[@key=$key]" />
      </xsl:call-template>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="matrix.row">
    <xsl:param name="id" select="''" />
    <tr>
      <th><xsl:value-of select="$id"/></th>
      <xsl:for-each select="/report/results">
        <xsl:variable name="column" select="annotation[@key=$key]" />
        <xsl:call-template name="result">
          <xsl:with-param name="id" select="$id" />
          <xsl:with-param name="column" select="$column" />
        </xsl:call-template>
      </xsl:for-each>
    </tr>
  </xsl:template>
    
  <!-- Generate a single cell in the result matrix -->
  <xsl:template name="result">
    <xsl:param name="id" select="''" />
    <xsl:param name="column" select="''" />
    <xsl:variable name="result"
                  select="/report/results[annotation[@key=$key]=$column]/result[@id=$id]" />
    <xsl:variable name="outcome">
      <xsl:choose>
        <!-- Is there an expectation for this test ? -->
        <xsl:when test="$result/@outcome and 
                        $result/annotation/@name='qmtest.expected_outcome'">
          
          <xsl:variable name="exp.outcome"
                        select="normalize-space($result/annotation[@name='qmtest.expected_outcome'])"/>
          <xsl:message><xsl:value-of select="$exp.outcome" /></xsl:message>
          <xsl:variable name="exp.cause"
                        select="$result/annotation[@name='qmtest.expected_cause']"/>
          <xsl:choose>
            <xsl:when test="$result/@outcome='PASS' and 
                            $exp.outcome='&#34;PASS&#34;'">pass</xsl:when>
            <xsl:when test="$result/@outcome='PASS' and 
                            $exp.outcome='&#34;FAIL&#34;'">xpass</xsl:when>
            <xsl:when test="$result/@outcome='FAIL' and 
                            $exp.outcome='&#34;PASS&#34;'">xfail</xsl:when>
            <xsl:when test="$result/@outcome='FAIL' and 
                            $exp.outcome='&#34;FAIL&#34;'">fail</xsl:when>
            <xsl:otherwise>untested</xsl:otherwise>
          </xsl:choose>
        </xsl:when>
        <xsl:otherwise>
          <!-- No expectation. -->
          <xsl:choose>
            <xsl:when test="$result/@outcome='PASS'">pass</xsl:when>
            <xsl:when test="$result/@outcome='FAIL'">fail</xsl:when>
            <xsl:otherwise>untested</xsl:otherwise>
          </xsl:choose>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <td class="{$outcome}">
      <xsl:choose>
        <xsl:when test="$result/@outcome">
          <xsl:variable name="document">
            <xsl:call-template name="detail.document.name">
              <xsl:with-param name="name" select="$column" />
            </xsl:call-template>
          </xsl:variable>
          <a href="{$document}#{$id}">
            <xsl:value-of select="$outcome" />
          </a>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$outcome" />
        </xsl:otherwise>
      </xsl:choose>
    </td>
  </xsl:template>
    
  <xsl:template name="detail">
    <xsl:for-each select="/report/results[annotation/@key=$key]/result">
      <xsl:call-template name="result.detail" />
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="result.detail">
    <div class="{@outcome}">
      <p class="heading"><a name="{@id}" /><xsl:value-of select="@id" /></p>
    <xsl:if test="annotation[not(contains($excluded.annotations, @name))]">
    <table>
      <tbody>
        <tr><th>Annotation</th><th>Value</th></tr>
        <xsl:for-each select="annotation[not(contains($excluded.annotations, @name))]">
          <tr>
            <th><xsl:value-of select="@name" /></th>
            <td><pre><xsl:value-of select="." xsl:disable-output-escaping="yes"/></pre></td>
          </tr>
        </xsl:for-each>
      </tbody>
    </table>
    </xsl:if>
    </div>
  </xsl:template>

  <xsl:template name="detail.document.name">
    <xsl:param name="name" select="''" />
    <xsl:value-of select="translate(concat(normalize-space($name),'.html'), ':', '_')" />
  </xsl:template>

</xsl:stylesheet>

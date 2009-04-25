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

  <!-- use 'favicon' if defined -->
  <xsl:param name="favicon" select="''" />

  <!-- 'stylesheet' is used to identify results (result files) -->
  <xsl:param name="stylesheet" select="'report.css'" />

  <!-- 'key' is used to identify results (result files) -->
  <xsl:param name="key" select="'qmtest.run.end_time'" />

  <!-- Result annotations not to include in the report -->
  <xsl:param name="excluded.annotations" select="''" />

  <!-- Generate the main report page -->
  <xsl:template name="report.main.page">
    <html>
      <head>
        <title><xsl:value-of select="$title" /></title>
        <xsl:if test="$favicon">
          <link rel="shortcut icon" href="{$favicon}"/>
        </xsl:if>
        <link type="text/css" rel="stylesheet" href="{$stylesheet}"/>
      </head>
      <body>
        <h1><xsl:value-of select="$title" /></h1>
        <p>(generated on <xsl:value-of select="date:date-time()"/>)</p>
        <!-- summary -->
        <div class="summary">
          <p class="heading">Summary</p>
          <xsl:call-template name="summary" />
        </div>
        <xsl:if test="subdirectory">
          <xsl:call-template name="subdirectory"/>
        </xsl:if>
        <!-- generate test matrix -->
        <xsl:if test="item[@kind='test']">
          <h2>Tests</h2>
          <xsl:call-template name="matrix">
            <xsl:with-param name="kind" select="'test'"/>
          </xsl:call-template>
        </xsl:if>
        <!-- generate resource matrix -->
        <xsl:if test="item[@kind='resource_setup']">
          <h2>Resources</h2>
          <xsl:call-template name="matrix">
            <xsl:with-param name="kind" select="'resource_setup'"/>
          </xsl:call-template>
        </xsl:if>
      </body>
    </html>
  </xsl:template>

  <xsl:template name="subdirectory">
    <div class="directories">
      <h2>Subdirectories</h2>
      <table>
        <xsl:for-each select="subdirectory">
          <tr>
            <th><a href="{@name}/index.html"><xsl:value-of select="@name"/></a></th>
            <td>
              <table class="score">
                <tr>
                  <xsl:variable name="passes" select="(100 * count(*/result[@outcome='PASS'])) div count(*/result)"/>
                  <xsl:variable name="failures" select="(100 * count(*/result[@outcome='FAIL'])) div count(*/result)"/>
                  <xsl:if test="$passes != '0'">
                    <td class="pass" style="width:{}%">&#160;</td>
                  </xsl:if>
                  <xsl:if test="$failures != '0'">
                    <td class="fail" style="width:{(100 * count(*/result[@outcome='FAIL'])) div count(*/result)}%">&#160;</td>
                  </xsl:if>
                </tr>
              </table>
            </td>
            <td>
              (<xsl:value-of select="count(*/result[@outcome='PASS'])"/> passes, <xsl:value-of select="count(*/result[@outcome='FAIL'])"/> failures)
            </td>
          </tr>
          <xsl:apply-templates select="."/>
        </xsl:for-each>
      </table>
    </div>  
  </xsl:template>
  
  <!-- This is the template that generates the subdirectory report pages -->
  <xsl:template name="report.page">
    <common:document href="{@name}/index.html" method="xml" indent="yes" encoding="ISO-8859-1">
      <xsl:apply-templates select="subdirectory"/>
      <xsl:variable name="title">
        Results for subdirectory <xsl:value-of select="@name"/>
      </xsl:variable>
      <html>
        <head>
          <title><xsl:value-of select="$title" /></title>
          <xsl:variable name="path">
            <xsl:for-each select="ancestor-or-self::subdirectory">
              <xsl:copy-of select="'../'"/>
            </xsl:for-each>
          </xsl:variable>
          <link type="text/css" rel="stylesheet" href="{$path}{$stylesheet}"/>
        </head>
        <body>
          <h1><xsl:value-of select="$title" /></h1>
          <h2>Directory <xsl:value-of select="@name"/></h2>
          <xsl:if test="subdirectory">
            <xsl:call-template name="subdirectory"/>
          </xsl:if>
          <!-- generate test matrix -->
          <xsl:if test="item[@kind='test']">
            <h2>Tests</h2>
            <xsl:call-template name="matrix">
              <xsl:with-param name="kind" select="'test'"/>
            </xsl:call-template>
          </xsl:if>
          <!-- generate resource matrix -->
          <xsl:if test="item[@kind='resource_setup']">
            <h2>Resources</h2>
            <xsl:call-template name="matrix">
              <xsl:with-param name="kind" select="'resource_setup'"/>
            </xsl:call-template>
          </xsl:if>
          <!-- generate detailed pages, one per result set. -->
          <xsl:call-template name="details" />
        </body>
      </html>
    </common:document>
  </xsl:template>

  <xsl:template name="detail.page">
    <xsl:param name="run" select="1"/>
    <xsl:param name="directory" select="''"/>
    <xsl:variable name="id" select="annotation[@key=$key]"/>
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
          <xsl:variable name="path">
            <xsl:for-each select="$directory/ancestor-or-self::subdirectory">
              <xsl:copy-of select="'../'"/>
            </xsl:for-each>
          </xsl:variable>
          <link type="text/css" rel="stylesheet" href="{$path}{$stylesheet}"/>
        </head>
        <body>
          <h1><xsl:value-of select="$title" /></h1>
          <xsl:for-each select="$directory/item/result[$run]">
            <xsl:call-template name="result.detail"/>
          </xsl:for-each>
        </body>
      </html>
    </common:document>
  </xsl:template>

  <!-- QMTest report generation templates.

       These templates shouldn't be required to be redefined
   -->

  <xsl:template match="/">
    <!-- write meta data about test runs... -->
    <xsl:apply-templates select="/report/results"/>
  </xsl:template>

  <xsl:template match="results">
    <xsl:call-template name="report.main.page"/>
    <!-- generate detailed pages, one per result set. -->
    <xsl:call-template name="details"/>
  </xsl:template>

  <xsl:template match="subdirectory">
    <xsl:call-template name="report.page"/>
    <!-- generate detailed pages, one per result set. -->
    <xsl:call-template name="details"/>
  </xsl:template>

  <xsl:template name="summary">
    <p><xsl:value-of select="count(/report/results//item/result)"/> tests</p>
    <p><xsl:value-of select="count(/report/results//item/result[@outcome='PASS'])"/> passes</p>
    <p><xsl:value-of select="count(/report/results//item/result[@outcome='FAIL'])"/> failures</p>
  </xsl:template>

  <xsl:template name="matrix">
    <xsl:param name="kind" select="''"/>
    <!-- generate a test matrix for the items in the current directory -->
    <table>
      <tbody>
        <tr>
          <th></th>
          <xsl:for-each select="/report/runs/run">
            <th><xsl:value-of select="annotation[@key=$key]"/></th>
          </xsl:for-each>
        </tr>
        <xsl:for-each select="item[@kind=$kind]">
          <xsl:variable name="id" select="@id"/>
          <tr>
            <th><xsl:value-of select="$id"/></th>
            <xsl:for-each select="result">
              <xsl:call-template name="result">
                <xsl:with-param name="id" select="$id"/>
                <xsl:with-param name="run" select="position()"/>
              </xsl:call-template>
            </xsl:for-each>
          </tr>
        </xsl:for-each>
      </tbody>
    </table>
  </xsl:template>

  <xsl:template name="details">
    <xsl:variable name="directory" select="."/>
    <xsl:for-each select="/report/runs/run">
      <xsl:call-template name="detail.page">
        <xsl:with-param name="run" select="position()"/>
        <xsl:with-param name="directory" select="$directory"/>
      </xsl:call-template>
    </xsl:for-each>
  </xsl:template>

  <!-- Generate a single cell in the result matrix -->
  <xsl:template name="result">
    <xsl:param name="id" select="''" />
    <xsl:param name="run" select="''" />
    <!--<xsl:variable name="result"
                  select="/report/results[annotation[@key=$key]=$column]/result[@id=$id]" />-->
    <xsl:variable name="outcome">
      <xsl:choose>
        <!-- Is there an expectation for this test ? -->
        <xsl:when test="@outcome and 
                        annotation/@name='qmtest.expected_outcome'">
          
          <xsl:variable name="exp.outcome"
                        select="normalize-space(annotation[@name='qmtest.expected_outcome'])"/>
          <xsl:variable name="exp.cause"
                        select="annotation[@name='qmtest.expected_cause']"/>
          <xsl:choose>
            <xsl:when test="@outcome='PASS' and 
                            $exp.outcome='&#34;PASS&#34;'">pass</xsl:when>
            <xsl:when test="@outcome='PASS' and 
                            $exp.outcome='&#34;FAIL&#34;'">xpass</xsl:when>
            <xsl:when test="@outcome='FAIL' and 
                            $exp.outcome='&#34;PASS&#34;'">xfail</xsl:when>
            <xsl:when test="@outcome='FAIL' and 
                            $exp.outcome='&#34;FAIL&#34;'">fail</xsl:when>
            <xsl:otherwise>untested</xsl:otherwise>
          </xsl:choose>
        </xsl:when>
        <xsl:otherwise>
          <!-- No expectation. -->
          <xsl:choose>
            <xsl:when test="@outcome='PASS'">pass</xsl:when>
            <xsl:when test="@outcome='FAIL'">fail</xsl:when>
            <xsl:otherwise>untested</xsl:otherwise>
          </xsl:choose>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <td class="{$outcome}">
      <xsl:choose>
        <xsl:when test="@outcome">
          <xsl:variable name="document">
            <xsl:call-template name="detail.document.name">
              <xsl:with-param name="name">
                <xsl:value-of select="/report/runs/run[$run]/annotation[@key=$key]"/>
              </xsl:with-param>
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
    
  <xsl:template name="result.detail">
    <div class="{@outcome}">
      <p class="heading"><a name="{../@id}" /><xsl:value-of select="../@id" /></p>
    <xsl:if test="annotation[not(contains($excluded.annotations, @name))]">
    <table>
      <tbody>
        <tr><th>Annotation</th><th>Value</th></tr>
        <xsl:for-each select="annotation[not(contains($excluded.annotations, @name))]">
          <tr>
            <th><xsl:value-of select="@name" /></th>
            <td><xsl:value-of select="." xsl:disable-output-escaping="yes"/></td>
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

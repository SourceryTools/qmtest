##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Support information for qualified Dublin Core Metadata.

$Id: dcterms.py 66902 2006-04-12 20:16:30Z philikon $
"""
__docformat__ = 'restructuredtext'

from zope.dublincore import dcsv

# useful namespace URIs
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

W3CDTF = "W3CDTF"


def splitEncoding(name):
    if "." not in name:
        return name, None
    parts = name.split(".")
    if parts[-1] in encodings:
        if len(parts) == 2:
            return parts
        else:
            return ".".join(parts[:-1]), parts[-1]
    else:
        return name, None


# The type validator function must raise an exception if the value
# passed isn't valid for the type being check, other just return.

_dcmitypes = {}
for x in ("Collection Dataset Event Image InteractiveResource"
          " Service Software Sound Text PhysicalObject").split():
    _dcmitypes[x.lower()] = x
del x

def check_dcmitype(value):
    if value.lower() not in _dcmitypes:
        raise ValueError("%r not a valid DCMIType")

def check_imt(value):
    pass

def check_iso639_2(value):
    pass

def check_rfc1766(value):
    pass

def check_uri(value):
    pass

def check_point(value):
    pass

def check_iso3166(value):
    pass

def check_box(value):
    pass

def check_tgn(value):
    pass

_period_fields = "name start end scheme".split()

def check_period(value):
    # checks a Period in DCSV format; see:
    # http://dublincore.org/documents/dcmi-period/
    items = dcsv.decode(value)
    d = dcsv.createMapping(items)
    for k in d:
        if k not in _period_fields:
            raise ValueError("unknown field label %r" % k)
    if d.get("scheme", W3CDTF).upper() == W3CDTF:
        if "start" in d:
            check_w3cdtf(d["start"])
        if "end" in d:
            check_w3cdtf(d["end"])

def check_w3cdtf(value):
    pass

def check_rfc3066(value):
    pass

encodings = {
    # name --> (allowed for, validator|None),
    "LCSH":     (("Subject",), None),
    "MESH":     (("Subject",), None),
    "DDC":      (("Subject",), None),
    "LCC":      (("Subject",), None),
    "UDC":      (("Subject",), None),
    "DCMIType": (("Type",), check_dcmitype),
    "IMT":      (("Format",), check_imt),
    "ISO639-2": (("Language",), check_iso639_2),
    "RFC1766":  (("Language",), check_rfc1766),
    "URI":      (("Identifier", "Relation", "Source",), check_uri),
    "Point":    (("Coverage.Spatial",), check_point),
    "ISO3166":  (("Coverage.Spatial",), check_iso3166),
    "Box":      (("Coverage.Spatial",), check_box),
    "TGN":      (("Coverage.Spatial",), check_tgn),
    "Period":   (("Coverage.Temporal",), check_period),
    W3CDTF:     (("Coverage.Temporal", "Date",), check_w3cdtf),
    "RFC3066":  (("Language",), check_rfc3066),
    }


name_to_element = {
    # unqualified DCMES 1.1
    "Title":         ("dc:title",         ""),
    "Creator":       ("dc:creator",       ""),
    "Subject":       ("dc:subject",       ""),
    "Description":   ("dc:description",   ""),
    "Publisher":     ("dc:publisher",     ""),
    "Contributor":   ("dc:contributor",   ""),
    "Date":          ("dc:date",          "dcterms:"+W3CDTF),
    "Type":          ("dc:type",          ""),
    "Format":        ("dc:format",        ""),
    "Identifier":    ("dc:identifier",    ""),
    "Source":        ("dc:source",        ""),
    "Language":      ("dc:language",      ""),
    "Relation":      ("dc:relation",      ""),
    "Coverage":      ("dc:coverage",      ""),
    "Rights":        ("dc:rights",        ""),

    # qualified DCMES 1.1 (directly handled by Zope)
    "Date.Created":  ("dcterms:created",  "dcterms:"+W3CDTF),
    "Date.Modified": ("dcterms:modified", "dcterms:"+W3CDTF),

    # qualified DCMES 1.1 (not used by Zope)
    "Audience":                      ("dcterms:audience", ""),
    "Audience.Education Level":      ("dcterms:educationLevel", ""),
    "Audience.Mediator":             ("dcterms:mediator", ""),
    "Coverage.Spatial":              ("dcterms:spatial", ""),
    "Coverage.Temporal":             ("dcterms:temporal", ""),
    "Date.Accepted":                 ("dcterms:accepted", "dcterms:"+W3CDTF),
    "Date.Available":                ("dcterms:available", "dcterms:"+W3CDTF),
    "Date.Copyrighted":              ("dcterms:copyrighted","dcterms:"+W3CDTF),
    "Date.Issued":                   ("dcterms:issued", "dcterms:"+W3CDTF),
    "Date.Submitted":                ("dcterms:submitted", "dcterms:"+W3CDTF),
    "Date.Valid":                    ("dcterms:valid", "dcterms:"+W3CDTF),
    "Description.Abstract":          ("dcterms:abstract", ""),
    "Description.Table Of Contents": ("dcterms:tableOfContents", ""),
    "Format":                        ("dc:format", ""),
    "Format.Extent":                 ("dcterms:extent", ""),
    "Format.Medium":                 ("dcterms:medium", ""),
    "Identifier.Bibliographic Citation": ("dcterms:bibliographicCitation", ""),
    "Relation.Is Version Of":        ("dcterms:isVersionOf", ""),
    "Relation.Has Version":          ("dcterms:hasVersion", ""),
    "Relation.Is Replaced By":       ("dcterms:isReplacedBy", ""),
    "Relation.Replaces":             ("dcterms:replaces", ""),
    "Relation.Is Required By":       ("dcterms:isRequiredBy", ""),
    "Relation.Requires":             ("dcterms:requires", ""),
    "Relation.Is Part Of":           ("dcterms:isPartOf", ""),
    "Relation.Has Part":             ("dcterms:hasPart", ""),
    "Relation.Is Referenced By":     ("dcterms:isReferencedBy", ""),
    "Relation.References":           ("dcterms:references", ""),
    "Relation.Is Format Of":         ("dcterms:isFormatOf", ""),
    "Relation.Has Format":           ("dcterms:hasFormat", ""),
    "Relation.Conforms To":          ("dcterms:conformsTo", ""),
    "Rights.Access Rights":          ("dcterms:accessRights", ""),
    "Title.Alternative":             ("dcterms:alternative", ""),
    }

_prefix_to_ns = {
    "dc": DC_NS,
    "dcterms": DCTERMS_NS,
    # "xsi": XSI_NS,    dont' use this for element names, only attrs
    }

element_to_name = {}
for name, (qname, attrs) in name_to_element.iteritems():
    prefix, localname = qname.split(":")
    elem_name = _prefix_to_ns[prefix], localname
    element_to_name[elem_name] = name
    name_to_element[name] = (elem_name, attrs)

<!-- The value of an integer field.  -->
<!ELEMENT integer (#PCDATA)>

<!-- The value of a text field.  -->
<!ELEMENT text (#PCDATA)>

<!-- The value of a set field.  -->
<!ELEMENT set ((integer | text | attachment | enumeral)*)>

<!-- The value of an attachment field.  -->
<!ELEMENT attachment ((description?, 
                       mimetype?, 
                       filename?, 
                       (location | data))?)>

<!-- A text description of an attachment.  -->
<!ELEMENT description (#PCDATA)>

<!-- The MIME type of an attachment.  -->
<!ELEMENT mimetype (#PCDATA)>

<!-- The file name from which an attachment was uploaded.  -->
<!ELEMENT filename (#PCDATA)>

<!-- The database-specific location where an attachment is stored.  -->
<!ELEMENT location (#PCDATA)>

<!-- Inline attachment data.  -->
<!ELEMENT data (#PCDATA)>
<!ATTLIST data encoding CDATA "none">

<!-- The value of an enumeral field.  -->
<!ELEMENT enumeral (#PCDATA)>


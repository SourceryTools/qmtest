===================================================
Internationalization (I18n) and Localization (L10n)
===================================================

This document assumes that you have a Zope 3 checkout and the gettext
utilities installed.


Creating/Updating Message Catalog Template (POT) Files
------------------------------------------------------

Whenever you've made a change to Zope that affects the i18n messages,
you need to re-extract i18n messages from the code.  To do that,
execute ``i18nextract.py`` from the ``utilities`` directory of your
Zope 3 checkout:

  $ python utilities/i18nextract.py -d zope -p src/zope -o app/locales

This will update the ``zope.pot`` file.  Make sure that the checkout's
``src`` directory is part of your ``PYTHONPATH`` environment variable.

After that, you need to merge those changes to all existing
translations.  You can do that by executing the ``i18nmergeall.py``
script from the ``utilities`` directory of your Zope 3 checkout:

  $ python utilities/i18nmergeall.py -l src/zope/app/locales


Translating
-----------

To translate messages you need to do the following steps:

1. If a translation for your language is already present and you just
   want to update, skip ahead to step 2.  If you want to start
   translation on a new language, you need to

   a) create a directory

        src/zope/app/locales/<lang_code>/LC_MESSAGES

      with the appropriate code for your language as <lang_code>.
      Note that the two letters specifying the language should always
      be lower case (e.g. 'pt'); if you additionally specify a region,
      those letters should be upper case (e.g. 'pt_BR').

   b) copy the ``zope.pot`` template file to
      ``<lang_code>/LC_MESSAGES/zope.po``.

   c) edit the PO header of the newly created ``zope.po`` file and
      fill in all the necessary information.

2. Translate messages within the PO file.  Make sure the gettext
   syntax stays intact.  Tools like poEdit and KBabel can help you.

3. Finally, when you're done translating, compile the PO file to its
   binary equivalent using the ``msgfmt`` tool:

   $ cd <lang_code>/LC_MESSAGES
   $ msgfmt -o zope.mo zope.po

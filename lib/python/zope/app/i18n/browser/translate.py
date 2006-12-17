##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Translation GUI

$Id: translate.py 26889 2004-08-04 04:00:36Z pruggera $
"""
__docformat__ = 'restructuredtext'

from zope.app.i18n.browser import BaseView

class Translate(BaseView):

    def getMessages(self):
        """Get messages"""
        filter = self.request.get('filter', '%')
        messages = []
        for msg_id in self.context.getMessageIds(filter):
            messages.append((msg_id, len(messages)))

        return messages


    def getTranslation(self, msgid, target_lang):
        return self.context.translate(msgid, target_language=target_lang)


    def getEditLanguages(self):
        '''get the languages that are selected for editing'''
        languages = self.request.cookies.get('edit_languages', '')
        return filter(None, languages.split(','))


    def editMessage(self):
        msg_id = self.request['msg_id']
        for language in self.getEditLanguages():
            msg = self.request['msg_lang_%s' %language]
            if msg != self.context.translate(msg_id,
                                             target_language=language):
                self.context.updateMessage(msg_id, msg, language)
        return self.request.response.redirect(self.request.URL[-1])


    def editMessages(self):
        # Handle new Messages
        for count in range(5):
            msg_id = self.request.get('new-msg_id-%i' %count, '')
            if msg_id:
                for language in self.getEditLanguages():
                    msg = self.request.get('new-%s-%i' %(language, count),
                                           msg_id)
                    self.context.addMessage(msg_id, msg, language)

        # Handle edited Messages
        keys = filter(lambda k: k.startswith('edit-msg_id-'),
                      self.request.keys())
        keys = map(lambda k: k[12:], keys)
        for key in keys:
            msg_id = self.request['edit-msg_id-'+key]
            for language in self.getEditLanguages():
                msg = self.request['edit-%s-%s' %(language, key)]
                if msg != self.context.translate(msg_id,
                                                 target_language=language):
                    self.context.updateMessage(msg_id, msg, language)

        return self.request.response.redirect(self.request.URL[-1])


    def deleteMessages(self, message_ids):
        for id in message_ids:
            msgid = self.request.form['edit-msg_id-%s' %id]
            for language in self.context.getAvailableLanguages():
                # Some we edit a language, but no translation exists...
                try:
                    self.context.deleteMessage(msgid, language)
                except KeyError:
                    pass
        return self.request.response.redirect(self.request.URL[-1])


    def addLanguage(self, language):
        self.context.addLanguage(language)
        return self.request.response.redirect(self.request.URL[-1])


    def changeEditLanguages(self, languages=[]):
        self.request.response.setCookie('edit_languages',
                                        ','.join(languages))
        return self.request.response.redirect(self.request.URL[-1])


    def changeFilter(self):
        filter = self.request.get('filter', '%')
        self.request.response.setCookie('filter', filter)
        return self.request.response.redirect(self.request.URL[-1])


    def deleteLanguages(self, languages):
        for language in languages:
            self.context.deleteLanguage(language)
        return self.request.response.redirect(self.request.URL[-1])

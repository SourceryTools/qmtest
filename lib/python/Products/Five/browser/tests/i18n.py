from zope.i18nmessageid import MessageFactory
_ = MessageFactory('fivetest')
from Products.Five import BrowserView

class I18nView(BrowserView):
    this_is_a_message = _(u'This is a message')


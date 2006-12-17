================
User Preferences
================

Implementing user preferences is usually a painful task, since it requires a
lot of custom coding and constantly changing preferences makes it hard to
maintain the data and UI. The `preference` package

  >>> from zope.app.preference import preference

eases this pain by providing a generic user preferences framework that uses
schemas to categorize and describe the preferences.

We also have to do some additional setup beforehand:

  >>> from zope.app.testing import setup

  >>> import zope.app.component.hooks
  >>> zope.app.component.hooks.setHooks()
  >>> setup.setUpTraversal()
  >>> setup.setUpSiteManagerLookup()


Preference Groups
------------------

Preferences are grouped in preference groups and the preferences inside a
group are specified via the preferences group schema:

  >>> import zope.interface
  >>> import zope.schema
  >>> class IZMIUserSettings(zope.interface.Interface):
  ...     """Basic User Preferences"""
  ...
  ...     email = zope.schema.TextLine(
  ...         title=u"E-mail Address",
  ...         description=u"E-mail Address used to send notifications")
  ...
  ...     skin = zope.schema.Choice(
  ...         title=u"Skin",
  ...         description=u"The skin that should be used for the ZMI.",
  ...         values=['Rotterdam', 'ZopeTop', 'Basic'],
  ...         default='Rotterdam')
  ...
  ...     showZopeLogo = zope.schema.Bool(
  ...         title=u"Show Zope Logo",
  ...         description=u"Specifies whether Zope logo should be displayed "
  ...                     u"at the top of the screen.",
  ...         default=True)

Now we can instantiate the preference group. Each preference group must have an
ID by which it can be accessed and optional title and description fields for UI
purposes:

  >>> settings = preference.PreferenceGroup(
  ...     "ZMISettings",
  ...     schema=IZMIUserSettings,
  ...     title=u"ZMI User Settings",
  ...     description=u"")

Note that the preferences group provides the interface it is representing:

  >>> IZMIUserSettings.providedBy(settings)
  True

and the id, schema and title of the group are directly available:

  >>> settings.__id__
  'ZMISettings'
  >>> settings.__schema__
  <InterfaceClass zope.app.preference.README.IZMIUserSettings>
  >>> settings.__title__
  u'ZMI User Settings'

So let's ask the preference group for the `skin` setting:

  >>> settings.skin #doctest:+ELLIPSIS
  Traceback (most recent call last):
  ...
  ComponentLookupError: 
  (<InterfaceClass ...interfaces.IPrincipalAnnotationUtility>, '')


So why did the lookup fail? Because we have not specified a principal yet, for
which we want to lookup the preferences. To do that, we have to create a new
interaction:

  >>> class Principal:
  ...     def __init__(self, id):
  ...         self.id = id
  >>> principal = Principal('zope.user')

  >>> class Participation:
  ...     interaction = None
  ...     def __init__(self, principal):
  ...         self.principal = principal

  >>> participation = Participation(principal)

  >>> import zope.security.management
  >>> zope.security.management.newInteraction(participation)

We also need a principal annotations utility, in which we store the settings:

  >>> from zope.app.principalannotation.interfaces import \
  ...         IPrincipalAnnotationUtility
  >>> class PrincipalAnnotations(dict):
  ...     zope.interface.implements(IPrincipalAnnotationUtility)
  ...
  ...     def getAnnotations(self, principal):
  ...         return self.setdefault(principal, {})

  >>> annotations = PrincipalAnnotations()

  >>> from zope.app.testing import ztapi
  >>> ztapi.provideUtility(IPrincipalAnnotationUtility, annotations)

Let's now try to access the settings again:

  >>> settings.skin
  'Rotterdam'

which is the default value, since we have not set it yet. We can now reassign
the value:

  >>> settings.skin = 'Basic'
  >>> settings.skin
  'Basic'

However, you cannot just enter any value, since it is validated before the
assignment:

  >>> settings.skin = 'MySkin'
  Traceback (most recent call last):
  ...
  ConstraintNotSatisfied: MySkin  


Preference Group Trees
----------------------

The preferences would not be very powerful, if you could create a full
preferences. So let's create a sub-group for our ZMI user settings, where we
can adjust the look and feel of the folder contents view:

  >>> import sets
  >>> class IFolderSettings(zope.interface.Interface):
  ...     """Basic User Preferences"""
  ...
  ...     shownFields = zope.schema.Set(
  ...         title=u"Shown Fields",
  ...         description=u"Fields shown in the table.",
  ...         value_type=zope.schema.Choice(['name', 'size', 'creator']),
  ...         default=sets.Set(['name', 'size']))
  ...
  ...     sortedBy = zope.schema.Choice(
  ...         title=u"Sorted By",
  ...         description=u"Data field to sort by.",
  ...         values=['name', 'size', 'creator'],
  ...         default='name')

  >>> folderSettings = preference.PreferenceGroup(
  ...     "ZMISettings.Folder",
  ...     schema=IFolderSettings,
  ...     title=u"Folder Content View Settings")

Note that the id was chosen so that the parent id is the prefix of the child's
id. Our new preference sub-group should now be available as an attribute or an
item on the parent group ...

  >>> settings.Folder
  Traceback (most recent call last):
  ...
  AttributeError: 'Folder' is not a preference or sub-group.

... but not before we register the groups as utilities:

  >>> from zope.app.preference import interfaces
  >>> from zope.app.testing import ztapi

  >>> ztapi.provideUtility(interfaces.IPreferenceGroup, settings,
  ...                      name='ZMISettings')
  >>> ztapi.provideUtility(interfaces.IPreferenceGroup, folderSettings,
  ...                      name='ZMISettings.Folder')

If we now try to lookup the sub-group again, we should be successful:

  >>> settings.Folder #doctest:+ELLIPSIS
  <zope.app.preference.preference.PreferenceGroup object at ...>

  >>> settings['Folder'] #doctest:+ELLIPSIS
  <zope.app.preference.preference.PreferenceGroup object at ...>

While the registry of the preference groups is flat, the careful naming of the
ids allows us to have a tree of preferences. Note that this pattern is very
similar to the way modules are handled in Python; they are stored in a flat
dictionary in ``sys.modules``, but due to the naming they appear to be in a
namespace tree.

While we are at it, there are also preference categories that can be compared
to Python packages. They basically are just a higher level grouping concept
that is used by the UI to better organize the preferences. A preference group
can be converted to a category by simply providing an additional interface:

  >>> zope.interface.alsoProvides(settings, interfaces.IPreferenceCategory)

  >>> interfaces.IPreferenceCategory.providedBy(settings)
  True


Default Preferences
-------------------

It sometimes desirable to define default settings on a site-by-site basis,
instead of just using the default value from the schema. The preferences
package provides a module
 
  >>> from zope.app.preference import default

that implements a default preferences provider that can be added as a unnamed
utility for each site. So the first step is to create a site:
  
  >>> root = setup.buildSampleFolderTree()
  >>> rsm = setup.createSiteManager(root, True)

Now we can register the default preference provider with the root site:

  >>> provider = setup.addUtility(rsm, '', 
  ...                             interfaces.IDefaultPreferenceProvider, 
  ...                             default.DefaultPreferenceProvider())

So before we set an explicit default value for a preference, the schema field
default is used:

  >>> settings.Folder.sortedBy
  'name'

But if we now set a new default value with the provider,

  >>> defaultFolder = provider.getDefaultPreferenceGroup('ZMISettings.Folder')
  >>> defaultFolder.sortedBy = 'size'

then the default of the setting changes:
  
  >>> settings.Folder.sortedBy
  'size'

The default preference providers also implicitly acquire default values from
parent sites. So if we make `folder1` a site and set it as the active site

  >>> folder1 = root['folder1']
  >>> sm1 = setup.createSiteManager(folder1, True)

and add a default provider there,

  >>> provider1 = setup.addUtility(sm1, '', 
  ...                              interfaces.IDefaultPreferenceProvider, 
  ...                              default.DefaultPreferenceProvider())

then we still get the root's default values, because we have not defined any
in the higher default provider:

  >>> settings.Folder.sortedBy
  'size'

But if we provide the new provider with a default value for `sortedBy`,

  >>> defaultFolder1 = provider1.getDefaultPreferenceGroup('ZMISettings.Folder')
  >>> defaultFolder1.sortedBy = 'creator'

then it is used instead:

  >>> settings.Folder.sortedBy
  'creator'

Of course, once the root site becomes our active site again

  >>> zope.app.component.hooks.setSite(root)

the default value of the root provider is used:

  >>> settings.Folder.sortedBy
  'size'

Of course, all the defaults in the world are not relevant anymore as soon as
the user actually provides a value:

  >>> settings.Folder.sortedBy = 'name'
  >>> settings.Folder.sortedBy
  'name'

Oh, and have I mentioned that entered values are always validated? So you
cannot just assign any old value:

  >>> settings.Folder.sortedBy = 'foo'
  Traceback (most recent call last):
  ...
  ConstraintNotSatisfied: foo

Finally, if the user deletes his/her explicit setting, we are back to the
default value:

  >>> del settings.Folder.sortedBy
  >>> settings.Folder.sortedBy
  'size'


Creating Preference Groups Using ZCML
-------------------------------------

If you are using the user preference system in Zope 3, you will not have to
manually setup the preference groups as we did above (of course). We will use
ZCML instead. First, we need to register the directives:

  >>> from zope.configuration import xmlconfig
  >>> import zope.app.preference
  >>> context = xmlconfig.file('meta.zcml', zope.app.preference)

Then the system sets up a root preference group:

  >>> context = xmlconfig.string('''
  ...     <configure
  ...         xmlns="http://namespaces.zope.org/zope"
  ...         i18n_domain="test">
  ...
  ...       <preferenceGroup
  ...           id=""
  ...           title="User Preferences" 
  ...           />
  ...
  ...     </configure>''', context)

Now we can use the preference system in its intended way. We access the folder
settings as follows:

  >>> from zope.app import zapi
  >>> prefs = zapi.getUtility(interfaces.IPreferenceGroup)
  >>> prefs.ZMISettings.Folder.sortedBy
  'size'

Let's register the ZMI settings again under a new name via ZCML:

  >>> context = xmlconfig.string('''
  ...     <configure
  ...         xmlns="http://namespaces.zope.org/zope"
  ...         i18n_domain="test">
  ...
  ...       <preferenceGroup
  ...           id="ZMISettings2"
  ...           title="ZMI Settings NG"
  ...           schema="zope.app.preference.README.IZMIUserSettings"
  ...           category="true"
  ...           />
  ...
  ...     </configure>''', context)

  >>> prefs.ZMISettings2 #doctest:+ELLIPSIS
  <zope.app.preference.preference.PreferenceGroup object at ...>

  >>> prefs.ZMISettings2.__title__
  u'ZMI Settings NG'

  >>> IZMIUserSettings.providedBy(prefs.ZMISettings2)
  True
  >>> interfaces.IPreferenceCategory.providedBy(prefs.ZMISettings2)
  True

And the tree can built again by carefully constructing the id:

  >>> context = xmlconfig.string('''
  ...     <configure
  ...         xmlns="http://namespaces.zope.org/zope"
  ...         i18n_domain="test">
  ...
  ...       <preferenceGroup
  ...           id="ZMISettings2.Folder"
  ...           title="Folder Settings"
  ...           schema="zope.app.preference.README.IFolderSettings"
  ...           />
  ...
  ...     </configure>''', context)

  >>> prefs.ZMISettings2 #doctest:+ELLIPSIS
  <zope.app.preference.preference.PreferenceGroup object at ...>

  >>> prefs.ZMISettings2.Folder.__title__
  u'Folder Settings'

  >>> IFolderSettings.providedBy(prefs.ZMISettings2.Folder)
  True
  >>> interfaces.IPreferenceCategory.providedBy(prefs.ZMISettings2.Folder)
  False


Simple Python-Level Access
--------------------------

If a site is set, getting the user preferences is very simple:

  >>> from zope.app.preference import UserPreferences
  >>> prefs2 = UserPreferences()
  >>> prefs2.ZMISettings.Folder.sortedBy
  'size'

This function is also commonly registered as an adapter,

  >>> from zope.location.interfaces import ILocation
  >>> ztapi.provideAdapter(ILocation, interfaces.IUserPreferences, 
  ...                      UserPreferences)

so that you can adapt any location to the user preferences:

  >>> prefs3 = interfaces.IUserPreferences(folder1)
  >>> prefs3.ZMISettings.Folder.sortedBy
  'creator'


Traversal
---------

Okay, so all these objects are nice, but they do not make it any easier to
access the preferences in page templates. Thus, a special traversal namespace
has been created that makes it very simple to access the preferences via a
traversal path. But before we can use the path expressions, we have to
register all necessary traversal components and the special `preferences`
namespace:

  >>> import zope.traversing.interfaces
  >>> ztapi.provideAdapter(None,
  ...                      zope.traversing.interfaces.ITraversable,
  ...                      preference.preferencesNamespace,
  ...                      'preferences')

We can now access the preferences as follows:

  >>> zapi.traverse(None, '++preferences++ZMISettings/skin')
  'Basic'
  >>> zapi.traverse(None, '++preferences++/ZMISettings/skin')
  'Basic'


Security
--------

You might already wonder under which permissions the preferences are
available. They are actually available publicly (`CheckerPublic`), but that
is not a problem, since the available values are looked up specifically for
the current user. And why should a user not have full access to his/her
preferences? 

Let's create a checker using the function that the security machinery is
actually using:

  >>> checker = preference.PreferenceGroupChecker(settings)
  >>> checker.permission_id('skin')
  Global(CheckerPublic,zope.security.checker)
  >>> checker.setattr_permission_id('skin')
  Global(CheckerPublic,zope.security.checker)

The id, title, description, and schema are publicly available for access,
but are not available for mutation at all:

  >>> checker.permission_id('__id__')
  Global(CheckerPublic,zope.security.checker)
  >>> checker.setattr_permission_id('__id__') is None
  True


The only way security could be compromised is when one could override the
annotations property. However, this property is not available for public
consumption at all, including read access:

  >>> checker.permission_id('annotation') is None
  True
  >>> checker.setattr_permission_id('annotation') is None
  True

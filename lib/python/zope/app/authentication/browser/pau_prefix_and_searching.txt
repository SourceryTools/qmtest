================================
Using a PAU Prefix and Searching
================================

This test confirms that both principals and groups can be searched for in
PAUs that have prefixes.

First we'll create a PAU with a prefix of `pau1_` and and register:

  >>> print http(r"""
  ... POST /++etc++site/default/+/AddPluggableAuthentication.html%3D HTTP/1.1
  ... Authorization: Basic bWdyOm1ncnB3
  ... Content-Length: 372
  ... Content-Type: multipart/form-data; boundary=---------------------------318183180122653
  ...
  ... -----------------------------318183180122653
  ... Content-Disposition: form-data; name="field.prefix"
  ...
  ... pau1_
  ... -----------------------------318183180122653
  ... Content-Disposition: form-data; name="UPDATE_SUBMIT"
  ...
  ... Add
  ... -----------------------------318183180122653
  ... Content-Disposition: form-data; name="add_input_name"
  ...
  ... PAU1
  ... -----------------------------318183180122653--
  ... """)
  HTTP/1.1 303 See Other
  ...

  >>> print http(r"""
  ... POST /++etc++site/default/PAU1/addRegistration.html HTTP/1.1
  ... Authorization: Basic bWdyOm1ncnB3
  ... Content-Length: 591
  ... Content-Type: multipart/form-data; boundary=---------------------------516441125097
  ...
  ... -----------------------------516441125097
  ... Content-Disposition: form-data; name="field.comment"
  ...
  ... 
  ... -----------------------------516441125097
  ... Content-Disposition: form-data; name="field.actions.register"
  ...
  ... Register
  ... -----------------------------516441125097--
  ... """)
  HTTP/1.1 303 See Other
  ...

Next we'll create and register a principal folder:

  >>> print http(r"""
  ... POST /++etc++site/default/PAU1/+/AddPrincipalFolder.html%3D HTTP/1.1
  ... Authorization: Basic bWdyOm1ncnB3
  ... Content-Length: 374
  ... Content-Type: multipart/form-data; boundary=---------------------------266241536215161
  ...
  ... -----------------------------266241536215161
  ... Content-Disposition: form-data; name="field.prefix"
  ...
  ... users_
  ... -----------------------------266241536215161
  ... Content-Disposition: form-data; name="UPDATE_SUBMIT"
  ...
  ... Add
  ... -----------------------------266241536215161
  ... Content-Disposition: form-data; name="add_input_name"
  ...
  ... Users
  ... -----------------------------266241536215161--
  ... """)
  HTTP/1.1 303 See Other
  ...

and add a principal that we'll later search for:

  >>> print http(r"""
  ... POST /++etc++site/default/PAU1/Users/+/AddPrincipalInformation.html%3D HTTP/1.1
  ... Authorization: Basic bWdyOm1ncnB3
  ... Content-Length: 686
  ... Content-Type: multipart/form-data; boundary=---------------------------300171485226567
  ...
  ... -----------------------------300171485226567
  ... Content-Disposition: form-data; name="field.login"
  ...
  ... bob
  ... -----------------------------300171485226567
  ... Content-Disposition: form-data; name="field.passwordManagerName"
  ...
  ... Plain Text
  ... -----------------------------300171485226567
  ... Content-Disposition: form-data; name="field.password"
  ...
  ... bob
  ... -----------------------------300171485226567
  ... Content-Disposition: form-data; name="field.title"
  ...
  ... Bob
  ... -----------------------------300171485226567
  ... Content-Disposition: form-data; name="field.description"
  ...
  ...
  ... -----------------------------300171485226567
  ... Content-Disposition: form-data; name="UPDATE_SUBMIT"
  ...
  ... Add
  ... -----------------------------300171485226567
  ... Content-Disposition: form-data; name="add_input_name"
  ...
  ...
  ... -----------------------------300171485226567--
  ... """)
  HTTP/1.1 303 See Other
  ...

Next, we'll add and register a group folder:

  >>> print http(r"""
  ... POST /++etc++site/default/PAU1/+/AddGroupFolder.html%3D HTTP/1.1
  ... Authorization: Basic bWdyOm1ncnB3
  ... Content-Length: 372
  ... Content-Type: multipart/form-data; boundary=---------------------------17420126702455
  ...
  ... -----------------------------17420126702455
  ... Content-Disposition: form-data; name="field.prefix"
  ...
  ... groups_
  ... -----------------------------17420126702455
  ... Content-Disposition: form-data; name="UPDATE_SUBMIT"
  ...
  ... Add
  ... -----------------------------17420126702455
  ... Content-Disposition: form-data; name="add_input_name"
  ...
  ... Groups
  ... -----------------------------17420126702455--
  ... """)
  HTTP/1.1 303 See Other
  ...

and add a group to search for:

  >>> print http(r"""
  ... POST /++etc++site/default/PAU1/Groups/+/AddGroupInformation.html%3D HTTP/1.1
  ... Authorization: Basic bWdyOm1ncnB3
  ... Content-Length: 485
  ... Content-Type: multipart/form-data; boundary=---------------------------323081358415654
  ...
  ... -----------------------------323081358415654
  ... Content-Disposition: form-data; name="field.title"
  ...
  ... Nice People
  ... -----------------------------323081358415654
  ... Content-Disposition: form-data; name="field.description"
  ...
  ...
  ... -----------------------------323081358415654
  ... Content-Disposition: form-data; name="UPDATE_SUBMIT"
  ...
  ... Add
  ... -----------------------------323081358415654
  ... Content-Disposition: form-data; name="add_input_name"
  ...
  ... nice
  ... -----------------------------323081358415654--
  ... """)
  HTTP/1.1 303 See Other
  ...

Since we're only searching in this test, we won't bother to add anyone to the
group.

Before we search, we need to register the two authenticator plugins with the
PAU:

  >>> print http(r"""
  ... POST /++etc++site/default/PAU1/@@configure.html HTTP/1.1
  ... Authorization: Basic bWdyOm1ncnB3
  ... Content-Length: 888
  ... Content-Type: multipart/form-data; boundary=---------------------------610310492754
  ...
  ... -----------------------------610310492754
  ... Content-Disposition: form-data; name="field.credentialsPlugins-empty-marker"
  ...
  ...
  ... -----------------------------610310492754
  ... Content-Disposition: form-data; name="field.authenticatorPlugins.to"
  ...
  ... R3JvdXBz
  ... -----------------------------610310492754
  ... Content-Disposition: form-data; name="field.authenticatorPlugins.to"
  ...
  ... VXNlcnM=
  ... -----------------------------610310492754
  ... Content-Disposition: form-data; name="field.authenticatorPlugins-empty-marker"
  ...
  ...
  ... -----------------------------610310492754
  ... Content-Disposition: form-data; name="UPDATE_SUBMIT"
  ...
  ... Change
  ... -----------------------------610310492754
  ... Content-Disposition: form-data; name="field.authenticatorPlugins"
  ...
  ... R3JvdXBz
  ... -----------------------------610310492754
  ... Content-Disposition: form-data; name="field.authenticatorPlugins"
  ...
  ... VXNlcnM=
  ... -----------------------------610310492754--
  ... """)
  HTTP/1.1 200 OK
  ...

Now we'll use the 'grant' interface of the root folder to search for all of
the available groups:

  >>> print http(r"""
  ... POST /@@grant.html HTTP/1.1
  ... Authorization: Basic bWdyOm1ncnB3
  ... Content-Length: 191
  ... Content-Type: application/x-www-form-urlencoded
  ... 
  ... field.principal.displayed=y&"""
  ... "field.principal.MC5Hcm91cHM_.field.search=&"
  ... "field.principal.MC5Hcm91cHM_.search=Search&"
  ... "field.principal.MC5Vc2Vycw__.field.search=&"
  ... "field.principal.MQ__.searchstring=")
  HTTP/1.1 200 OK
  ...
  <select name="field.principal.MC5Hcm91cHM_.selection">
  <option value="cGF1MV9ncm91cHNfbmljZQ__">Nice People</option>
  </select>
  ...

Note in the results that the dropdown box (i.e. the select element) has the
single group 'Nice People' that we added earlier.

Next, we'll use the same 'grant' interface to search for all of the available
principals:

  >>> print http(r"""
  ... POST /@@grant.html HTTP/1.1
  ... Authorization: Basic bWdyOm1ncnB3
  ... Content-Length: 255
  ... Content-Type: application/x-www-form-urlencoded
  ...
  ... field.principal.displayed=y&"""
  ... "field.principal.MC5Hcm91cHM_.field.search=&"
  ... "field.principal.MC5Hcm91cHM_.selection=cGF1MV9ncm91cHNfbmljZQ__&"
  ... "field.principal.MC5Vc2Vycw__.field.search=&"
  ... "field.principal.MC5Vc2Vycw__.search=Search&"
  ... "field.principal.MQ__.searchstring=")
  HTTP/1.1 200 OK
  ...
  <select name="field.principal.MC5Vc2Vycw__.selection">
  <option value="cGF1MV91c2Vyc18x">Bob</option>
  </select>
  ...

Note here the dropdown contains Bob, the principal we added earlier.

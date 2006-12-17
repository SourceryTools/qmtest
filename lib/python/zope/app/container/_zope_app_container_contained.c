/*############################################################################
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
############################################################################*/

#define _ZOPE_APP_CONTAINER_CONTAINED_C "$Id: _zope_app_container_contained.c 37889 2005-08-12 15:25:08Z fdrake $\n"

/* Contained Proxy Base class

 Contained proxies provide __parent__ and __name__ attributes for
 objects without them.

 There is something strange and, possibly cool, going on here, wrt
 persistence.  To reuse the base proxy implementation we don't treat
 the proxied object as part of the persistent state of the proxy.
 This means that the proxy still operates as a proxy even if it is a
 ghost.  

 The proxy will only be unghostified if you need to access one of the
 attributes provided by the proxy.

 */


#include "Python.h"
#include "persistent/cPersistence.h"

static PyObject *str_p_deactivate;

typedef struct {
  cPersistent_HEAD
  PyObject *po_weaklist;
  PyObject *proxy_object;
  PyObject *__parent__;
  PyObject *__name__;
} ProxyObject;

typedef struct {
    PyTypeObject *proxytype;
    int (*check)(PyObject *obj);
    PyObject *(*create)(PyObject *obj);
    PyObject *(*getobject)(PyObject *proxy);
} ProxyInterface;

#define OBJECT(O) ((PyObject*)(O))
#define Proxy_GET_OBJECT(ob)   (((ProxyObject *)(ob))->proxy_object)

#define CLEAR(O) \
  if (O) {PyObject *clr__tmp = O; O = NULL; Py_DECREF(clr__tmp); }

/* Supress inclusion of the original proxy.h */
#define _proxy_H_ 1

/* Incude the proxy C source */
#include "_zope_proxy_proxy.c"

#define SPECIAL(NAME) (                        \
    *(NAME) == '_' &&                          \
      (((NAME)[1] == 'p' && (NAME)[2] == '_')  \
       ||                                      \
       ((NAME)[1] == '_' && (                  \
         strcmp((NAME), "__parent__") == 0     \
         ||                                    \
         strcmp((NAME), "__name__") == 0       \
         ||                                    \
         strcmp((NAME), "__getstate__") == 0   \
         ||                                    \
         strcmp((NAME), "__setstate__") == 0   \
         ||                                    \
         strcmp((NAME), "__getnewargs__") == 0 \
         ||                                    \
         strcmp((NAME), "__reduce__") == 0     \
         ||                                    \
         strcmp((NAME), "__reduce_ex__") == 0  \
         ))                                    \
       ))
      
static PyObject *
CP_getattro(PyObject *self, PyObject *name)
{
  char *cname;

  cname = PyString_AsString(name);
  if (cname == NULL)
    return NULL;

  if (SPECIAL(cname))
    /* delegate to persistent */
    return cPersistenceCAPI->pertype->tp_getattro(self, name);

  /* Use the wrapper version to delegate */
  return wrap_getattro(self, name);
}

static int
CP_setattro(PyObject *self, PyObject *name, PyObject *v)
{
  char *cname;

  cname = PyString_AsString(name);
  if (cname == NULL)
    return -1;

  if (SPECIAL(cname))
    /* delegate to persistent */
    return cPersistenceCAPI->pertype->tp_setattro(self, name, v);

  /* Use the wrapper version to delegate */
  return wrap_setattro(self, name, v);
}

static PyObject *
CP_getstate(ProxyObject *self)
{
  return Py_BuildValue("OO", 
                       self->__parent__ ? self->__parent__ : Py_None,
                       self->__name__   ? self->__name__   : Py_None
                       );
}

static PyObject *
CP_getnewargs(ProxyObject *self)
{
  return Py_BuildValue("(O)", self->proxy_object);
}

static PyObject *
CP_setstate(ProxyObject *self, PyObject *state)
{
  PyObject *parent, *name;

  if(! PyArg_ParseTuple(state, "OO", &parent, &name))
    return NULL;

  CLEAR(self->__parent__);
  CLEAR(self->__name__);

  Py_INCREF(parent);
  Py_INCREF(name);

  self->__parent__ = parent;
  self->__name__ = name;

  Py_INCREF(Py_None);
  return Py_None;
}

static PyObject *
CP_reduce(ProxyObject *self)
{
  PyObject *result;
  if (! PER_USE(self))
    return NULL;
  result = Py_BuildValue("O(O)(OO)",
                         self->ob_type,
                         self->proxy_object,
                         self->__parent__ ? self->__parent__ : Py_None,
                         self->__name__   ? self->__name__   : Py_None
                         );
  PER_ALLOW_DEACTIVATION(self);
  return result;
}

static PyObject *
CP_reduce_ex(ProxyObject *self, PyObject *proto)
{
  return CP_reduce(self);
}

static PyObject *
CP__p_deactivate(ProxyObject *self)
{
  PyObject *result;

  result = PyObject_CallMethodObjArgs(OBJECT(cPersistenceCAPI->pertype), 
                                      str_p_deactivate,
                                      self, NULL);
  if (result == NULL)
    return NULL;

  if (self->jar && self->oid && self->state == cPersistent_UPTODATE_STATE)
    {
      Py_XDECREF(self->__parent__);
      self->__parent__ = NULL;
      Py_XDECREF(self->__name__);
      self->__name__ = NULL;
    }

    return result;
}


static PyMethodDef
CP_methods[] = {
  {"__getstate__", (PyCFunction)CP_getstate, METH_NOARGS, 
   "Get the object state"},
  {"__setstate__", (PyCFunction)CP_setstate, METH_O, 
   "Set the object state"},
  {"__getnewargs__", (PyCFunction)CP_getnewargs, METH_NOARGS, 
   "Get the arguments that must be passed to __new__"},
  {"__reduce__", (PyCFunction)CP_reduce, METH_NOARGS, 
   "Reduce the object to constituent parts."},
  {"__reduce_ex__", (PyCFunction)CP_reduce_ex, METH_O, 
   "Reduce the object to constituent parts."},
  {"_p_deactivate", (PyCFunction)CP__p_deactivate, METH_NOARGS, 
   "Deactivate the object."},
  {NULL, NULL},
};


/* Code to access structure members by accessing attributes */

#include "structmember.h"

static PyMemberDef CP_members[] = {
  {"__parent__", T_OBJECT, offsetof(ProxyObject, __parent__)},
  {"__name__", T_OBJECT, offsetof(ProxyObject, __name__)},
  {NULL}	/* Sentinel */
};

static int
CP_traverse(ProxyObject *self, visitproc visit, void *arg)
{
  if (cPersistenceCAPI->pertype->tp_traverse((PyObject *)self, visit, arg) < 0)
    return -1;
  if (self->proxy_object != NULL && visit(self->proxy_object, arg) < 0)
    return -1;
  if (self->__parent__ != NULL && visit(self->__parent__, arg) < 0)
    return -1;
  if (self->__name__ != NULL && visit(self->__name__, arg) < 0)
    return -1;
  
  return 0;
}

static int
CP_clear(ProxyObject *self)
{
  /* Drop references that may have created reference
     cycles. Immutable objects do not have to define this method
     since they can never directly create reference cycles. Note
     that the object must still be valid after calling this
     method (don't just call Py_DECREF() on a reference). The
     collector will call this method if it detects that this
     object is involved in a reference cycle.
  */
  if (cPersistenceCAPI->pertype->tp_clear != NULL)
    cPersistenceCAPI->pertype->tp_clear((PyObject*)self);
  
  CLEAR(self->proxy_object);
  CLEAR(self->__parent__);
  CLEAR(self->__name__);

  return 0;
}

static void
CP_dealloc(ProxyObject *self)
{
  if (self->po_weaklist != NULL)
    PyObject_ClearWeakRefs((PyObject *)self);

  CLEAR(self->proxy_object);
  CLEAR(self->__parent__);
  CLEAR(self->__name__);

  cPersistenceCAPI->pertype->tp_dealloc((PyObject*)self);
}

#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
init_zope_app_container_contained(void)
{
  PyObject *m;

  str_p_deactivate = PyString_FromString("_p_deactivate");
  if (str_p_deactivate == NULL)
    return;
        
  /* Try to fake out compiler nag function */
  if (0) init_zope_proxy_proxy();
  
  m = Py_InitModule3("_zope_app_container_contained", 
                     module_functions, module___doc__);

  if (m == NULL)
    return;

  if (empty_tuple == NULL)
    empty_tuple = PyTuple_New(0);

  /* Initialize the PyPersist_C_API and the type objects. */
  cPersistenceCAPI = PyCObject_Import("persistent.cPersistence", "CAPI");
  if (cPersistenceCAPI == NULL)
    return;

  ProxyType.tp_name = "zope.app.container.contained.ContainedProxyBase";
  ProxyType.ob_type = &PyType_Type;
  ProxyType.tp_base = cPersistenceCAPI->pertype;
  ProxyType.tp_getattro = CP_getattro;
  ProxyType.tp_setattro = CP_setattro;
  ProxyType.tp_members = CP_members;
  ProxyType.tp_methods = CP_methods;
  ProxyType.tp_traverse = (traverseproc) CP_traverse;
  ProxyType.tp_clear = (inquiry) CP_clear;
  ProxyType.tp_dealloc = (destructor) CP_dealloc;
  ProxyType.tp_weaklistoffset = offsetof(ProxyObject, po_weaklist);

  if (PyType_Ready(&ProxyType) < 0)
    return;

  Py_INCREF(&ProxyType);
  PyModule_AddObject(m, "ContainedProxyBase", (PyObject *)&ProxyType);
}

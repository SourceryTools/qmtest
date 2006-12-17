/*

 Copyright (c) 2003 Zope Corporation and Contributors.
 All Rights Reserved.

 This software is subject to the provisions of the Zope Public License,
 Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
 THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
 WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
 FOR A PARTICULAR PURPOSE.

*/

#include "Python.h"
#include "structmember.h"

#define CLEAR(O) if (O) {PyObject *t = O; O = 0; Py_DECREF(t); }

typedef struct {
    PyObject_HEAD
    PyObject *key;
    PyObject *args;
    PyObject *kw;
    PyObject *dict;
} localobject;

static PyTypeObject localtype;

static PyObject *
local_new(PyTypeObject *type, PyObject *args, PyObject *kw)
{
    	localobject *self;
        PyObject *tdict;

        if (type->tp_init == PyBaseObject_Type.tp_init
            && ((args && PyObject_IsTrue(args))
                ||
                (kw && PyObject_IsTrue(kw))
                )
            ) {
          	PyErr_SetString(PyExc_TypeError,
                          "Initialization arguments are not supported");
                return NULL;
        }

    	self = (localobject *)type->tp_alloc(type, 0);
        if (self == NULL)
          return NULL;

        Py_XINCREF(args);
        self->args = args;
        Py_XINCREF(kw);
        self->kw = kw;
        self->dict = NULL;      /* making sure */
        self->key = PyString_FromFormat("thread.local.%p", self);
        if (self->key == NULL) 
                goto err;

        self->dict = PyDict_New();
        if (self->dict == NULL)
                goto err;

        tdict = PyThreadState_GetDict();
        if (tdict == NULL) {
                PyErr_SetString(PyExc_SystemError,
                                "Couldn't get thread-state dictionary");
                goto err;
        }

        if (PyDict_SetItem(tdict, self->key, self->dict) < 0)
                goto err;
       
    	return (PyObject *)self;

 err:
        Py_DECREF(self);
        return NULL;
}

static int
local_traverse(localobject *self, visitproc visit, void *arg)
{
	if (self->args != NULL && visit(self->args, arg) < 0)
		return -1;
	if (self->kw != NULL && visit(self->kw, arg) < 0)
		return -1;
	if (self->dict != NULL && visit(self->dict, arg) < 0)
		return -1;
	return 0;
}

static int
local_clear(localobject *self)
{
  	CLEAR(self->key);
        CLEAR(self->args);
        CLEAR(self->kw);
        CLEAR(self->dict);
        return 0;
}

static void
local_dealloc(localobject *self)
{
        PyThreadState *tstate;
        if (self->key
            && (tstate = PyThreadState_Get())
            && tstate->interp) {
                for(tstate = PyInterpreterState_ThreadHead(tstate->interp);
                    tstate;
                    tstate = PyThreadState_Next(tstate)
                    ) 
                        if (tstate->dict &&
                            PyDict_GetItem(tstate->dict, self->key))
                                PyDict_DelItem(tstate->dict, self->key);
        }

  	local_clear(self);
        self->ob_type->tp_free((PyObject*)self);
}

static PyObject *
_ldict(localobject *self)
{
	PyObject *tdict, *ldict;

	tdict = PyThreadState_GetDict();
        if (tdict == NULL) {
        	PyErr_SetString(PyExc_SystemError,
                                "Couldn't get thread-state dictionary");
                return NULL;
        }

        ldict = PyDict_GetItem(tdict, self->key);
        if (ldict == NULL) {
        	ldict = PyDict_New(); /* we own ldict */

                if (ldict == NULL)
                	return NULL;
                else {
                        int i = PyDict_SetItem(tdict, self->key, ldict);
                        Py_DECREF(ldict); /* now ldict is borowed */
                        if (i < 0) 
                                return NULL;
                }

                CLEAR(self->dict);
                Py_INCREF(ldict);
                self->dict = ldict; /* still borrowed */

                if (self->ob_type->tp_init != PyBaseObject_Type.tp_init &&
                    self->ob_type->tp_init((PyObject*)self, 
                                           self->args, self->kw) < 0
                    ) {
                        /* we need to get rid of ldict from thread so
                           we create a new one the next time we do an attr
                           acces */
                        PyDict_DelItem(tdict, self->key);
                        return NULL;
                }
                
        }
        else if (self->dict != ldict) {
                CLEAR(self->dict);
                Py_INCREF(ldict);
                self->dict = ldict;
        }

  return ldict;
}

static PyObject *
local_getattro(localobject *self, PyObject *name)
{
	PyObject *ldict, *value;

        ldict = _ldict(self);
        if (ldict == NULL) 
        	return NULL;

        if (self->ob_type != &localtype)
                /* use generic lookup for subtypes */
                return PyObject_GenericGetAttr((PyObject *)self, name);

        /* Optimization: just look in dict ourselves */
        value = PyDict_GetItem(ldict, name);
        if (value == NULL) 
                /* Fall back on generic to get __class__ and __dict__ */
                return PyObject_GenericGetAttr((PyObject *)self, name);

        Py_INCREF(value);
        return value;
}

static int
local_setattro(localobject *self, PyObject *name, PyObject *v)
{
	PyObject *ldict;
        
        ldict = _ldict(self);
        if (ldict == NULL) 
          	return -1;

        return PyObject_GenericSetAttr((PyObject *)self, name, v);
}

static PyObject *
local_getdict(localobject *self, void *closure)
{
        if (self->dict == NULL) {
                PyErr_SetString(PyExc_AttributeError, "__dict__");
                return NULL;
        }

    	Py_INCREF(self->dict);
        return self->dict;
}

static PyGetSetDef local_getset[] = {
    {"__dict__", 
     (getter)local_getdict, (setter)0,
     "Local-data dictionary",
     NULL},
    {NULL}  /* Sentinel */
};

static PyTypeObject localtype = {
	PyObject_HEAD_INIT(NULL)
	/* ob_size           */ 0,
	/* tp_name           */ "zope.thread.local",
	/* tp_basicsize      */ sizeof(localobject),
	/* tp_itemsize       */ 0,
	/* tp_dealloc        */ (destructor)local_dealloc,
	/* tp_print          */ (printfunc)0,
	/* tp_getattr        */ (getattrfunc)0,
	/* tp_setattr        */ (setattrfunc)0,
	/* tp_compare        */ (cmpfunc)0,
	/* tp_repr           */ (reprfunc)0,
	/* tp_as_number      */ 0,
	/* tp_as_sequence    */ 0,
	/* tp_as_mapping     */ 0,
	/* tp_hash           */ (hashfunc)0,
	/* tp_call           */ (ternaryfunc)0,
	/* tp_str            */ (reprfunc)0,
        /* tp_getattro       */ (getattrofunc)local_getattro,
        /* tp_setattro       */ (setattrofunc)local_setattro,
        /* tp_as_buffer      */ 0,
        /* tp_flags          */ Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
	/* tp_doc            */ "Thread-local data",
        /* tp_traverse       */ (traverseproc)local_traverse,
        /* tp_clear          */ (inquiry)local_clear,
        /* tp_richcompare    */ (richcmpfunc)0,
        /* tp_weaklistoffset */ (long)0,
        /* tp_iter           */ (getiterfunc)0,
        /* tp_iternext       */ (iternextfunc)0,
        /* tp_methods        */ 0,
        /* tp_members        */ 0,
        /* tp_getset         */ local_getset,
        /* tp_base           */ 0,
        /* tp_dict           */ 0, /* internal use */
        /* tp_descr_get      */ (descrgetfunc)0,
        /* tp_descr_set      */ (descrsetfunc)0,
        /* tp_dictoffset     */ offsetof(localobject, dict),
        /* tp_init           */ (initproc)0,
        /* tp_alloc          */ (allocfunc)0,
        /* tp_new            */ (newfunc)local_new,
	/* tp_free           */ 0, /* Low-level free-mem routine */
	/* tp_is_gc          */ (inquiry)0, /* For PyObject_IS_GC */
};

/* End of code for local objects */
/* -------------------------------------------------------- */


/* List of methods defined in the module */

static struct PyMethodDef _zope_thread_methods[] = {

	{NULL,	 (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
init_zope_thread(void)
{
	PyObject *m;
        
        /* Initialize types: */
        if (PyType_Ready(&localtype) < 0)
        	return;
        
	/* Create the module and add the functions */
	m = Py_InitModule3("_zope_thread", _zope_thread_methods,
                           "zope.thread C implementation");

        if (m == NULL)
        	return;
      
        /* Add types: */
        if (PyModule_AddObject(m, "local", (PyObject *)&localtype) < 0)
        	return;
   }


/*****************************************************************************
*
* Copyright (c) 2003, 2004 Zope Corporation and Contributors.
* All Rights Reserved.
*
* This software is subject to the provisions of the Zope Public License,
* Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
* THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
* WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
* FOR A PARTICULAR PURPOSE.
*
******************************************************************************
Security Proxy Implementation

$Id: _proxy.c 67762 2006-04-30 13:56:45Z jim $
*/

#include <Python.h>
#include "zope.proxy/proxy.h"

static PyObject *__class__str = 0, *__name__str = 0, *__module__str = 0;

#define DECLARE_STRING(N) static PyObject *str_##N

DECLARE_STRING(__3pow__);
DECLARE_STRING(__call__);
DECLARE_STRING(check);
DECLARE_STRING(check_getattr);
DECLARE_STRING(check_setattr);
DECLARE_STRING(__cmp__);
DECLARE_STRING(__coerce__);
DECLARE_STRING(__contains__);
DECLARE_STRING(__delitem__);
DECLARE_STRING(__getitem__);
DECLARE_STRING(__getslice__);
DECLARE_STRING(__hash__);
DECLARE_STRING(__iter__);
DECLARE_STRING(__len__);
DECLARE_STRING(next);
DECLARE_STRING(__nonzero__);
DECLARE_STRING(op_abs);
DECLARE_STRING(op_add);
DECLARE_STRING(op_and);
DECLARE_STRING(op_div);
DECLARE_STRING(op_divmod);
DECLARE_STRING(op_float);
DECLARE_STRING(op_floordiv);
DECLARE_STRING(op_hex);
DECLARE_STRING(op_iadd);
DECLARE_STRING(op_iand);
DECLARE_STRING(op_idiv);
DECLARE_STRING(op_ifloordiv);
DECLARE_STRING(op_ilshift);
DECLARE_STRING(op_imod);
DECLARE_STRING(op_imul);
DECLARE_STRING(op_int);
DECLARE_STRING(op_invert);
DECLARE_STRING(op_ior);
DECLARE_STRING(op_ipow);
DECLARE_STRING(op_irshift);
DECLARE_STRING(op_isub);
DECLARE_STRING(op_itruediv);
DECLARE_STRING(op_ixor);
DECLARE_STRING(op_long);
DECLARE_STRING(op_lshift);
DECLARE_STRING(op_mod);
DECLARE_STRING(op_mul);
DECLARE_STRING(op_neg);
DECLARE_STRING(op_oct);
DECLARE_STRING(op_or);
DECLARE_STRING(op_pos);
DECLARE_STRING(op_radd);
DECLARE_STRING(op_rand);
DECLARE_STRING(op_rdiv);
DECLARE_STRING(op_rdivmod);
DECLARE_STRING(op_rfloordiv);
DECLARE_STRING(op_rlshift);
DECLARE_STRING(op_rmod);
DECLARE_STRING(op_rmul);
DECLARE_STRING(op_ror);
DECLARE_STRING(op_rrshift);
DECLARE_STRING(op_rshift);
DECLARE_STRING(op_rsub);
DECLARE_STRING(op_rtruediv);
DECLARE_STRING(op_rxor);
DECLARE_STRING(op_sub);
DECLARE_STRING(op_truediv);
DECLARE_STRING(op_xor);
DECLARE_STRING(__pow__);
DECLARE_STRING(proxy);
DECLARE_STRING(__repr__);
DECLARE_STRING(__rpow__);
DECLARE_STRING(__setitem__);
DECLARE_STRING(__setslice__);
DECLARE_STRING(__str__);

typedef struct {
  ProxyObject proxy;
  PyObject *proxy_checker;
} SecurityProxy;

#define CLEAR(O) if (O) {PyObject *t = O; O = 0; Py_DECREF(t); }

#undef Proxy_Check
#define Proxy_Check(proxy) \
	PyObject_TypeCheck(proxy, &SecurityProxyType)

static PyTypeObject SecurityProxyType;

/*
 * Machinery to call the checker.
 */

static int
check(SecurityProxy *self, PyObject *meth, PyObject *name)
{
  PyObject *r;

  /* If the checker has __setitem__, we call it's slot rather than
     calling check or check_getattr. Why? Because calling operator slots
     is much faster than calling methods and security checks are done so
     often that speed matters.  So we have this hack of using
     almost-arbitrary operations to represent methods that we call
     alot.  */
  if (self->proxy_checker->ob_type->tp_as_mapping != NULL
      && self->proxy_checker->ob_type->tp_as_mapping->mp_ass_subscript != NULL
      && meth != str_check_setattr)
    return self->proxy_checker->ob_type->tp_as_mapping->
      mp_ass_subscript(self->proxy_checker, self->proxy.proxy_object, name);

  r = PyObject_CallMethodObjArgs(self->proxy_checker, meth, 
                                 self->proxy.proxy_object, name, 
                                 NULL);
  if (r == NULL)
    return -1;

  Py_DECREF(r);
  return 0;
}

/* If the checker has __getitem__, we call it's slot rather than
   calling proxy. Why? Because calling operator slots
   is much faster than calling methods and security checks are done so
   often that speed matters.  So we have this hack of using
   almost-arbitrary operations to represent methods that we call
   alot.  */
#define PROXY_RESULT(self, result) \
if (result != NULL) { \
  PyObject *tmp; \
  if (self->proxy_checker->ob_type->tp_as_mapping != NULL \
      && self->proxy_checker->ob_type->tp_as_mapping->mp_subscript != NULL) \
    tmp = self->proxy_checker->ob_type->tp_as_mapping-> \
      mp_subscript(self->proxy_checker, result); \
  else \
    tmp = PyObject_CallMethodObjArgs(self->proxy_checker, str_proxy, \
                                     result, NULL); \
  Py_DECREF(result); \
  result = tmp; \
}

typedef PyObject *(*function1)(PyObject *);

static PyObject *
check1(SecurityProxy *self, PyObject *opname, function1 operation)
{
  PyObject *result = NULL;

  if (check(self, str_check, opname) >= 0) {
    result = operation(self->proxy.proxy_object);
    PROXY_RESULT(self, result);
  }
  return result;
}

static PyObject *
check2(PyObject *self, PyObject *other,
       PyObject *opname, PyObject *ropname, binaryfunc operation)
{
  PyObject *result = NULL;

  if (Proxy_Check(self)) 
    {
      if (check((SecurityProxy*)self, str_check, opname) >= 0)
        {
          result = operation(((SecurityProxy*)self)->proxy.proxy_object, 
                             other);
          PROXY_RESULT(((SecurityProxy*)self), result);
        }
    }
  else if (Proxy_Check(other)) 
    {
      if (check((SecurityProxy*)other, str_check, ropname) >= 0)
        {
          result = operation(self, 
                             ((SecurityProxy*)other)->proxy.proxy_object);
    
          PROXY_RESULT(((SecurityProxy*)other), result);
        }
    }
  else 
    {
      Py_INCREF(Py_NotImplemented);
      return Py_NotImplemented;
    }

  return result;
}

static PyObject *
check2i(SecurityProxy *self, PyObject *other,
	PyObject *opname, binaryfunc operation)
{
  PyObject *result = NULL;

  if (check(self, str_check, opname) >= 0) 
    {
      result = operation(self->proxy.proxy_object, other);
      if (result == self->proxy.proxy_object) 
        {
          /* If the operation was really carried out inplace,
             don't create a new proxy, but use the old one. */
          Py_DECREF(result);
          Py_INCREF((PyObject *)self);
          result = (PyObject *)self;
        }
      else 
        PROXY_RESULT(self, result);
    }
  return result;
}

#define UNOP(NAME, CALL) \
	static PyObject *proxy_##NAME(PyObject *self) \
	{ return check1((SecurityProxy *)self, str_op_##NAME, CALL); }

#define BINOP(NAME, CALL) \
	static PyObject *proxy_##NAME(PyObject *self, PyObject *other) \
	{ return check2(self, other, str_op_##NAME, str_op_r##NAME, CALL); }

#define INPLACE(NAME, CALL) \
	static PyObject *proxy_i##NAME(PyObject *self, PyObject *other) \
	{ return check2i((SecurityProxy *)self, other, str_op_i##NAME, CALL); }


/*
 * Slot methods.
 */

static PyObject *
proxy_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  static char *kwlist[] = {"object", "checker", 0};
  SecurityProxy *self;
  PyObject *object;
  PyObject *checker;

  if (!PyArg_ParseTupleAndKeywords(args, kwds,
                                   "OO:_Proxy.__new__", kwlist,
                                   &object, &checker))
    return NULL;

  if (checker == Py_None)
    {
      PyErr_SetString(PyExc_ValueError, "None passed as proxy checker");
      return NULL;
    }

  self = (SecurityProxy *)type->tp_alloc(type, 0);
  if (self == NULL)
    return NULL;
  Py_INCREF(object);
  Py_INCREF(checker);
  self->proxy.proxy_object = object;
  self->proxy_checker = checker;
  return (PyObject *)self;
}

/* This is needed to avoid calling the base class tp_init, which we
   don't need. */
static int
proxy_init(PyObject *self, PyObject *args, PyObject *kw)
{
  return 0;
}

static int
proxy_clear(SecurityProxy *self)
{
  CLEAR(self->proxy_checker);
  SecurityProxyType.tp_base->tp_clear((PyObject*)self);
  return 0;
}

static void
proxy_dealloc(SecurityProxy *self)
{
  proxy_clear(self);
  SecurityProxyType.tp_base->tp_dealloc((PyObject*)self);
}

static int
proxy_traverse(SecurityProxy *self, visitproc visit, void *arg)
{
  if (visit(self->proxy.proxy_object, arg) < 0)
    return -1;
  if (visit(self->proxy_checker, arg) < 0)
    return -1;
  return 0;
}

static PyObject *
proxy_richcompare(SecurityProxy* self, PyObject* other, int op)
{
  PyObject *result = NULL;

  result = PyObject_RichCompare(self->proxy.proxy_object, other, op);
  if (result == Py_True || result == Py_False)
    return result;
  PROXY_RESULT(self, result);
  return result;
}

static PyObject *
proxy_iter(SecurityProxy *self)
{
  PyObject *result = NULL;

  if (check(self, str_check, str___iter__) >= 0) 
    {
      result = PyObject_GetIter(self->proxy.proxy_object);
      PROXY_RESULT(self, result);
    }
  return result;
}

static PyObject *
proxy_iternext(SecurityProxy *self)
{
  PyObject *result = NULL;

  if (check(self, str_check_getattr, str_next) >= 0) 
    {
      result = PyIter_Next(self->proxy.proxy_object);
      PROXY_RESULT(self, result);
    }
  return result;
}

static PyObject *
proxy_getattro(SecurityProxy *self, PyObject *name)
{
  PyObject *result = NULL;

  if (check(self, str_check_getattr, name) >= 0) 
    {
      result = PyObject_GetAttr(self->proxy.proxy_object, name);
      PROXY_RESULT(self, result);
    }
  return result;
}

static int
proxy_setattro(SecurityProxy *self, PyObject *name, PyObject *value)
{
  if (check(self, str_check_setattr, name) >= 0)
    return PyObject_SetAttr(self->proxy.proxy_object, name, value);
  return -1;
}

static PyObject *
default_repr(PyObject *object)
{
  PyObject *klass, *name = 0, *module = 0, *result = 0;
  char *sname, *smodule;

  klass = PyObject_GetAttr(object, __class__str);
  if (klass == NULL)
    return NULL;

  name  = PyObject_GetAttr(klass, __name__str);
  if (name == NULL)
    goto err;
  sname = PyString_AsString(name);
  if (sname == NULL)
    goto err;

  module = PyObject_GetAttr(klass, __module__str);
  if (module != NULL) {
    smodule = PyString_AsString(module);
    if (smodule == NULL)
      goto err;
    result = PyString_FromFormat("<security proxied %s.%s instance at %p>",
                                 smodule, sname, object);
  }
  else {
    PyErr_Clear();
    result = PyString_FromFormat("<security proxied %s instance at %p>",
                                 sname, object);
  }

 err:
  Py_DECREF(klass);
  Py_XDECREF(name);
  Py_XDECREF(module);
  
  return result;
}

static PyObject *
proxy_str(SecurityProxy *self)
{
  PyObject *result = NULL;

  if (check(self, str_check, str___str__) >= 0) 
    {
      result = PyObject_Str(self->proxy.proxy_object);
    }
  else 
    {
      PyErr_Clear();
      result = default_repr(self->proxy.proxy_object);
    }
  return result;
}

static PyObject *
proxy_repr(SecurityProxy *self)
{
  PyObject *result = NULL;

  if (check(self, str_check, str___repr__) >= 0) {
    result = PyObject_Repr(self->proxy.proxy_object);
  }
  else {
    PyErr_Clear();
    result = default_repr(self->proxy.proxy_object);
  }
  return result;
}

static int
proxy_compare(SecurityProxy *self, PyObject *other)
{
  return PyObject_Compare(self->proxy.proxy_object, other);
}

static long
proxy_hash(SecurityProxy *self)
{
  return PyObject_Hash(self->proxy.proxy_object);
}

static PyObject *
proxy_call(SecurityProxy *self, PyObject *args, PyObject *kwds)
{
  PyObject *result = NULL;

  if (check(self, str_check, str___call__) >= 0) 
    {
      result = PyObject_Call(self->proxy.proxy_object, args, kwds);
      PROXY_RESULT(self, result);
    }
  return result;
}

/*
 * Number methods.
 */

#define NUMBER_METHOD(M) \
static PyObject * \
call_##M(PyObject *self) \
{ \
  PyNumberMethods *nb = self->ob_type->tp_as_number; \
  if (nb == NULL || nb->nb_##M == NULL) { \
    PyErr_SetString(PyExc_TypeError, \
                    "object can't be converted to " #M); \
    return NULL; \
  } \
  return nb->nb_##M(self); \
}

NUMBER_METHOD(int)
NUMBER_METHOD(long)
NUMBER_METHOD(float)
NUMBER_METHOD(oct)
NUMBER_METHOD(hex)

static PyObject *
call_ipow(PyObject *self, PyObject *other)
{
  /* PyNumber_InPlacePower has three args.  How silly. :-) */
  return PyNumber_InPlacePower(self, other, Py_None);
}

BINOP(add, PyNumber_Add)
BINOP(sub, PyNumber_Subtract)
BINOP(mul, PyNumber_Multiply)
BINOP(div, PyNumber_Divide)
BINOP(mod, PyNumber_Remainder)
BINOP(divmod, PyNumber_Divmod)

static PyObject *
proxy_pow(PyObject *self, PyObject *other, PyObject *modulus)
{
  PyObject *result = NULL;

  if (Proxy_Check(self)) 
    {
      if (check((SecurityProxy*)self, str_check, str___pow__) >= 0)
        {
          result = PyNumber_Power(((SecurityProxy*)self)->proxy.proxy_object,
                                  other, modulus);
          PROXY_RESULT(((SecurityProxy*)self), result);
        }
    }
  else if (Proxy_Check(other)) 
    {
      if (check((SecurityProxy*)other, str_check, str___rpow__) >= 0)
        {      
          result = PyNumber_Power(self, 
                                  ((SecurityProxy*)other)->proxy.proxy_object, 
                                  modulus);
          PROXY_RESULT(((SecurityProxy*)other), result);
        }
    }
  else if (modulus != NULL && Proxy_Check(modulus)) 
    {
      if (check((SecurityProxy*)modulus, str_check, str___3pow__) >= 0)
        {      
          result = PyNumber_Power(self, other, 
                               ((SecurityProxy*)modulus)->proxy.proxy_object);
          PROXY_RESULT(((SecurityProxy*)modulus), result);
        }
    }
  else {
    Py_INCREF(Py_NotImplemented);
    return Py_NotImplemented;
  }
  return result;
}

BINOP(lshift, PyNumber_Lshift)
BINOP(rshift, PyNumber_Rshift)
BINOP(and, PyNumber_And)
BINOP(xor, PyNumber_Xor)
BINOP(or, PyNumber_Or)

static int
proxy_coerce(PyObject **p_self, PyObject **p_other)
{
  PyObject *self = *p_self;
  PyObject *other = *p_other;

  assert(Proxy_Check(self));

  if (check((SecurityProxy*)self, str_check, str___coerce__) >= 0) 
    {
      PyObject *left = ((SecurityProxy*)self)->proxy.proxy_object;
      PyObject *right = other;
      int r;
      r = PyNumber_CoerceEx(&left, &right);
      if (r != 0)
        return r;
      /* Now left and right have been INCREF'ed.
         Any new value that comes out is proxied;
         any unchanged value is left unchanged. */
      if (left == ((SecurityProxy*)self)->proxy.proxy_object) {
        /* Keep the old proxy */
        Py_DECREF(left);
        Py_INCREF(self);
        left = self;
      }
      else {
        PROXY_RESULT(((SecurityProxy*)self), left);
        if (left == NULL) {
          Py_DECREF(right);
          return -1;
        }
      }
      if (right != other) {
        PROXY_RESULT(((SecurityProxy*)self), right);
        if (right == NULL) {
          Py_DECREF(left);
          return -1;
        }
      }
      *p_self = left;
      *p_other = right;
      return 0;
    }
  return -1;
}

UNOP(neg, PyNumber_Negative)
UNOP(pos, PyNumber_Positive)
UNOP(abs, PyNumber_Absolute)

static int
proxy_nonzero(PyObject *self)
{
  return PyObject_IsTrue(((SecurityProxy*)self)->proxy.proxy_object);
}

UNOP(invert, PyNumber_Invert)
UNOP(int, call_int)
UNOP(long, call_long)
UNOP(float, call_float)
UNOP(oct, call_oct)
UNOP(hex, call_hex)

INPLACE(add, PyNumber_InPlaceAdd)
INPLACE(sub, PyNumber_InPlaceSubtract)
INPLACE(mul, PyNumber_InPlaceMultiply)
INPLACE(div, PyNumber_InPlaceDivide)
INPLACE(mod, PyNumber_InPlaceRemainder)
INPLACE(pow, call_ipow)
INPLACE(lshift, PyNumber_InPlaceLshift)
INPLACE(rshift, PyNumber_InPlaceRshift)
INPLACE(and, PyNumber_InPlaceAnd)
INPLACE(xor, PyNumber_InPlaceXor)
INPLACE(or, PyNumber_InPlaceOr)

BINOP(floordiv, PyNumber_FloorDivide)
BINOP(truediv, PyNumber_TrueDivide)
INPLACE(floordiv, PyNumber_InPlaceFloorDivide)
INPLACE(truediv, PyNumber_InPlaceTrueDivide)

/*
 * Sequence methods.
 */

static int
proxy_length(SecurityProxy *self)
{
  if (check(self, str_check, str___len__) >= 0)
    return PyObject_Length(self->proxy.proxy_object);
  return -1;
}

/* sq_item and sq_ass_item may be called by PySequece_{Get,Set}Item(). */
static PyObject *proxy_getitem(SecurityProxy *, PyObject *);
static int proxy_setitem(SecurityProxy *, PyObject *, PyObject *);

static PyObject *
proxy_igetitem(SecurityProxy *self, int i)
{
  PyObject *key = PyInt_FromLong(i);
  PyObject *res = NULL;

  if (key != NULL) {
    res = proxy_getitem(self, key);
    Py_DECREF(key);
  }
  return res;
}


static int
proxy_isetitem(SecurityProxy *self, int i, PyObject *value)
{
  PyObject *key = PyInt_FromLong(i);
  int res = -1;

  if (key != NULL) {
    res = proxy_setitem(self, key, value);
    Py_DECREF(key);
  }
  return res;
}

static PyObject *
proxy_slice(SecurityProxy *self, int start, int end)
{
  PyObject *result = NULL;

  if (check(self, str_check, str___getslice__) >= 0) {
    result = PySequence_GetSlice(self->proxy.proxy_object, start, end);
    PROXY_RESULT(self, result);
  }
  return result;
}

static int
proxy_ass_slice(SecurityProxy *self, int i, int j, PyObject *value)
{
  if (check(self, str_check, str___setslice__) >= 0)
    return PySequence_SetSlice(self->proxy.proxy_object, i, j, value);
  return -1;
}

static int
proxy_contains(SecurityProxy *self, PyObject *value)
{
  if (check(self, str_check, str___contains__) >= 0)
    return PySequence_Contains(self->proxy.proxy_object, value);
  return -1;
}

/*
 * Mapping methods.
 */

static PyObject *
proxy_getitem(SecurityProxy *self, PyObject *key)
{
  PyObject *result = NULL;

  if (check(self, str_check, str___getitem__) >= 0) 
    {
      result = PyObject_GetItem(self->proxy.proxy_object, key);
      PROXY_RESULT(self, result);
    }
  return result;
}

static int
proxy_setitem(SecurityProxy *self, PyObject *key, PyObject *value)
{
  if (value == NULL) {
    if (check(self, str_check, str___delitem__) >= 0)
      return PyObject_DelItem(self->proxy.proxy_object, key);
  }
  else {
    if (check(self, str_check, str___setitem__) >= 0)
      return PyObject_SetItem(self->proxy.proxy_object, key, value);
  }
  return -1;
}

/*
 * Normal methods.
 */

static PyNumberMethods
proxy_as_number = {
	proxy_add,				/* nb_add */
	proxy_sub,				/* nb_subtract */
	proxy_mul,				/* nb_multiply */
	proxy_div,				/* nb_divide */
	proxy_mod,				/* nb_remainder */
	proxy_divmod,				/* nb_divmod */
	proxy_pow,				/* nb_power */
	proxy_neg,				/* nb_negative */
	proxy_pos,				/* nb_positive */
	proxy_abs,				/* nb_absolute */
	proxy_nonzero,				/* nb_nonzero */
	proxy_invert,				/* nb_invert */
	proxy_lshift,				/* nb_lshift */
	proxy_rshift,				/* nb_rshift */
	proxy_and,				/* nb_and */
	proxy_xor,				/* nb_xor */
	proxy_or,				/* nb_or */
	proxy_coerce,				/* nb_coerce */
	proxy_int,				/* nb_int */
	proxy_long,				/* nb_long */
	proxy_float,				/* nb_float */
	proxy_oct,				/* nb_oct */
	proxy_hex,				/* nb_hex */

	/* Added in release 2.0 */
	/* These require the Py_TPFLAGS_HAVE_INPLACEOPS flag */
	proxy_iadd,				/* nb_inplace_add */
	proxy_isub,				/* nb_inplace_subtract */
	proxy_imul,				/* nb_inplace_multiply */
	proxy_idiv,				/* nb_inplace_divide */
	proxy_imod,				/* nb_inplace_remainder */
	(ternaryfunc)proxy_ipow,		/* nb_inplace_power */
	proxy_ilshift,				/* nb_inplace_lshift */
	proxy_irshift,				/* nb_inplace_rshift */
	proxy_iand,				/* nb_inplace_and */
	proxy_ixor,				/* nb_inplace_xor */
	proxy_ior,				/* nb_inplace_or */

	/* Added in release 2.2 */
	/* These require the Py_TPFLAGS_HAVE_CLASS flag */
	proxy_floordiv,				/* nb_floor_divide */
	proxy_truediv,				/* nb_true_divide */
	proxy_ifloordiv,			/* nb_inplace_floor_divide */
	proxy_itruediv,				/* nb_inplace_true_divide */
};

static PySequenceMethods
proxy_as_sequence = {
  (inquiry)proxy_length,				/* sq_length */
  0,					/* sq_concat */
  0,					/* sq_repeat */
  (intargfunc)proxy_igetitem,		        /* sq_item */
  (intintargfunc)proxy_slice,	       	/* sq_slice */
  (intobjargproc)proxy_isetitem,	/* sq_ass_item */
  (intintobjargproc)proxy_ass_slice,	/* sq_ass_slice */
  (objobjproc)proxy_contains,		/* sq_contains */
};

static PyMappingMethods
proxy_as_mapping = {
  (inquiry)proxy_length,				/* mp_length */
  (binaryfunc)proxy_getitem,				/* mp_subscript */
  (objobjargproc)proxy_setitem,				/* mp_ass_subscript */
};

static char proxy_doc[] = "\
Security proxy class.  Constructor: _Proxy(object, checker)\n\
where 'object' is an arbitrary object, and 'checker' is an object\n\
whose signature is described by the IChecker interface.\n\
A checker should have the following methods:\n\
  check(object, operation) # operation is e.g. '__add__' or '__hash__'\n\
  check_getattr(object, name)\n\
  check_setattr(object, name)\n\
  proxy(object)\n\
The check methods should raise an exception if the operation is\n\
disallowed.  The proxy method should return a proxy for the object\n\
if one is needed, otherwise the object itself.\n\
";

statichere PyTypeObject
SecurityProxyType = {
  PyObject_HEAD_INIT(NULL)
  0,
  "zope.security._proxy._Proxy",
  sizeof(SecurityProxy),
  0,
  (destructor)proxy_dealloc,				/* tp_dealloc */
  0,					/* tp_print */
  0,					/* tp_getattr */
  0,					/* tp_setattr */
  (cmpfunc)proxy_compare,				/* tp_compare */
  (reprfunc)proxy_repr,				/* tp_repr */
  &proxy_as_number,			/* tp_as_number */
  &proxy_as_sequence,			/* tp_as_sequence */
  &proxy_as_mapping,			/* tp_as_mapping */
  (hashfunc)proxy_hash,				/* tp_hash */
  (ternaryfunc)proxy_call,				/* tp_call */
  (reprfunc)proxy_str,				/* tp_str */
  (getattrofunc)proxy_getattro,				/* tp_getattro */
  (setattrofunc)proxy_setattro,				/* tp_setattro */
  0,					/* tp_as_buffer */
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_CHECKTYPES |
  Py_TPFLAGS_HAVE_GC,		/* tp_flags */
  proxy_doc,				/* tp_doc */
  (traverseproc)proxy_traverse,				/* tp_traverse */
  0,					/* tp_clear */
  (richcmpfunc)proxy_richcompare,			/* tp_richcompare */
  0,					/* tp_weaklistoffset */
  (getiterfunc)proxy_iter,				/* tp_iter */
  (iternextfunc)proxy_iternext,				/* tp_iternext */
  0,					/* tp_methods */
  0,					/* tp_members */
  0,					/* tp_getset */
  0,					/* tp_base */
  0,					/* tp_dict */
  0,					/* tp_descr_get */
  0,					/* tp_descr_set */
  0,					/* tp_dictoffset */
	proxy_init,				/* tp_init */
	0, /*PyType_GenericAlloc,*/		/* tp_alloc */
	proxy_new,				/* tp_new */
	0, /*_PyObject_GC_Del,*/		/* tp_free */
};

static PyObject *
module_getChecker(PyObject *self, PyObject *arg)
{
  PyObject *result;

  if (!Proxy_Check(arg)) {
    PyErr_SetString(PyExc_TypeError,
                    "getChecker argument must be a _Proxy");
    return NULL;
  }
  result = ((SecurityProxy*)arg)->proxy_checker;
  Py_INCREF(result);
  return result;
}

static PyObject *
module_getObject(PyObject *self, PyObject *arg)
{
  PyObject *result;

  if (!Proxy_Check(arg))
    result = arg;
  else
    result = ((SecurityProxy*)arg)->proxy.proxy_object;
  
  Py_INCREF(result);
  return result;
}

static PyMethodDef
module_functions[] = {
  {"getChecker", module_getChecker, METH_O, "get checker from proxy"},
  {"getObject", module_getObject, METH_O, 
   "Get the proxied object\n\nReturn the original object if not proxied."},
  {NULL}
};

static char
module___doc__[] = "Security proxy implementation.";

void
init_proxy(void)
{
  PyObject *m;

  if (Proxy_Import() < 0)
    return;

#define INIT_STRING(S) \
if((str_##S = PyString_InternFromString(#S)) == NULL) return
#define INIT_STRING_OP(S) \
if((str_op_##S = PyString_InternFromString("__" #S "__")) == NULL) return

  INIT_STRING(__3pow__);
  INIT_STRING(__call__);
  INIT_STRING(check);
  INIT_STRING(check_getattr);
  INIT_STRING(check_setattr);
  INIT_STRING(__cmp__);
  INIT_STRING(__coerce__);
  INIT_STRING(__contains__);
  INIT_STRING(__delitem__);
  INIT_STRING(__getitem__);
  INIT_STRING(__getslice__);
  INIT_STRING(__hash__);
  INIT_STRING(__iter__);
  INIT_STRING(__len__);
  INIT_STRING(next);
  INIT_STRING(__nonzero__);
  INIT_STRING_OP(abs);
  INIT_STRING_OP(add);
  INIT_STRING_OP(and);
  INIT_STRING_OP(div);
  INIT_STRING_OP(divmod);
  INIT_STRING_OP(float);
  INIT_STRING_OP(floordiv);
  INIT_STRING_OP(hex);
  INIT_STRING_OP(iadd);
  INIT_STRING_OP(iand);
  INIT_STRING_OP(idiv);
  INIT_STRING_OP(ifloordiv);
  INIT_STRING_OP(ilshift);
  INIT_STRING_OP(imod);
  INIT_STRING_OP(imul);
  INIT_STRING_OP(int);
  INIT_STRING_OP(invert);
  INIT_STRING_OP(ior);
  INIT_STRING_OP(ipow);
  INIT_STRING_OP(irshift);
  INIT_STRING_OP(isub);
  INIT_STRING_OP(itruediv);
  INIT_STRING_OP(ixor);
  INIT_STRING_OP(long);
  INIT_STRING_OP(lshift);
  INIT_STRING_OP(mod);
  INIT_STRING_OP(mul);
  INIT_STRING_OP(neg);
  INIT_STRING_OP(oct);
  INIT_STRING_OP(or);
  INIT_STRING_OP(pos);
  INIT_STRING_OP(radd);
  INIT_STRING_OP(rand);
  INIT_STRING_OP(rdiv);
  INIT_STRING_OP(rdivmod);
  INIT_STRING_OP(rfloordiv);
  INIT_STRING_OP(rlshift);
  INIT_STRING_OP(rmod);
  INIT_STRING_OP(rmul);
  INIT_STRING_OP(ror);
  INIT_STRING_OP(rrshift);
  INIT_STRING_OP(rshift);
  INIT_STRING_OP(rsub);
  INIT_STRING_OP(rtruediv);
  INIT_STRING_OP(rxor);
  INIT_STRING_OP(sub);
  INIT_STRING_OP(truediv);
  INIT_STRING_OP(xor);
  INIT_STRING(__pow__);
  INIT_STRING(proxy);
  INIT_STRING(__repr__);
  INIT_STRING(__rpow__);
  INIT_STRING(__setitem__);
  INIT_STRING(__setslice__);
  INIT_STRING(__str__);
  

  __class__str = PyString_FromString("__class__");
  if (! __class__str) return;
  
  __name__str = PyString_FromString("__name__");
  if (! __name__str) return;
  
  __module__str = PyString_FromString("__module__");
  if (! __module__str) return;
  
  SecurityProxyType.ob_type = &PyType_Type;
  SecurityProxyType.tp_alloc = PyType_GenericAlloc;
  SecurityProxyType.tp_free = _PyObject_GC_Del;
  SecurityProxyType.tp_base = &ProxyType;
  if (PyType_Ready(&SecurityProxyType) < 0)
    return;
  
  m = Py_InitModule3("_proxy", module_functions, module___doc__);
  if (m == NULL)
    return;
  
  Py_INCREF(&SecurityProxyType);
  PyModule_AddObject(m, "_Proxy", (PyObject *)&SecurityProxyType);
}

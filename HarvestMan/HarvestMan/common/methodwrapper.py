# -- coding: latin-1
""" methodwrapper.py - Module which provides a meta-class level
implementation for method wrappers. The metaclasses provided here
specifically wrap pre_* and post_* methods defined in classes
and wrap them around the original method.

Any class which wants to auto-implement pre and post callbacks
need to set their __metaclass__ attribute to the type
MethodWrapperMetaClass. This has to be done at the time of
defining the class.

This module provides the function set_method_wrapper which
sets a given method as a pre or post callback method on a class.

Created Anand B Pillai <abpillai at gmail dot com> Feb 17 2007

Copyright (C) 2007 Anand B Pillai.
"""

from new import function

class MethodWrapperBaseMetaClass(type):
    """ A base meta class for method wrappers """
    
    # This class allows wrapping pre_ and post_ callbacks
    # (methods) around a method. Original code courtesy
    # Eiffel method wrapper implementation in Python
    # subversion trunk @
    # http://svn.python.org/view/python/trunk/Demo/newmetaclasses/Eiffel.py
    
    def my_new(cls, *args, **kwargs):
        cls.convert_methods(cls.__dict__)
        return object.__new__(cls)
    
    def __init__(cls, name, bases, dct):
        super(MethodWrapperBaseMetaClass, cls).__init__(name, bases, dct)
        cls.__new__ = cls.my_new
        
    def convert_methods(cls, dict):
        """Replace functions in dict with MethodWrapper wrappers.

        The dict is modified in place.

        If a method ends in _pre or _post, it is removed from the dict
        regardless of whether there is a corresponding method.
        """
        # find methods with pre or post conditions
        methods = []
        for k, v in dict.iteritems():
            if k.startswith('pre_') or k.startswith('post_'):
                assert isinstance(v, function)
            elif isinstance(v, function):
                methods.append(k)
        for m in methods:
            pre = dict.get("pre_%s_callback" % m)
            post = dict.get("post_%s_callback" % m)
            if pre or post:
                setattr(cls, m, cls.make_wrapper_method(dict[m], pre, post))

class MethodWrapperMetaClass(MethodWrapperBaseMetaClass):
    # an implementation of the "MethodWrapper" meta class that uses nested functions

    @staticmethod
    def make_wrapper_method(func, pre, post):
        def method(self, *args, **kwargs):
            if pre:
                pre(self, *args, **kwargs)
            x = func(self, *args, **kwargs)
            if post:
                post(self, *args, **kwargs)
            return x

        if func.__doc__:
            method.__doc__ = func.__doc__

        return method

def set_wrapper_method(klass, method, callback, where='post'):
    """ Set callback method 'callback' on the method with
    the given name 'method' on class 'klass'. If the last
    argument is 'post' the method is inserted as a post-callback.
    If the last argument is 'pre', it is inserted as a pre-callback.
    """
    
    # Note: 'method' is the method name, not the method object

    # Set callback
    if where=='post':
        setattr(klass, 'post_' + method + '_callback', callback)
    elif where=='pre':
        setattr(klass, 'pre_' + method + '_callback', callback)        

def test():
    class MyClass(object):
        __metaclass__ = MethodWrapperMetaClass
        
        def f(self):
            print 'F called'
            pass

    def myfunc1(self):
        print 'Myfunc#1 called'

    def myfunc2(self):
        print 'Myfunc#2 called'


    set_wrapper_method(MyClass, 'f', myfunc1, 'pre')    
    set_wrapper_method(MyClass, 'f', myfunc2, 'post')

    c = MyClass()
    c.f()

if __name__=="__main__":
    test()
    

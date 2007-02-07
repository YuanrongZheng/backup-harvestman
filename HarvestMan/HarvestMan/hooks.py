""" Module allowing developer extensions(plugins) to HarvestMan.
This module makes it possible to hook into the execution
flow of HarvestMan, making it easy to extend and customize
it.

Created by Anand B Pillai <abpillai@gmail.com> Feb 1 07.

"""

from singleton import Singleton

class HarvestManHooksException(Exception):
    """ Exception class for HarvestManHooks class """
    pass

class HarvestManHooks(Singleton):
    """ Class which manages pluggable hooks for HarvestMan """
    
    supported_modules = ('crawler','harvestman', 'urlqueue', 'datamgr', 'connector')
    module_hooks = {}
    
    def __init__(self):
        self.run_hooks = {}

    def add_all_hooks(cls):

        for module in cls.supported_modules:
            # Get __hooks__ attribute from the module
            M = __import__(module)
            hooks = getattr(M, '__hooks__',{})
            # print hooks
            for hook in hooks.keys():
                cls.add_hook(module, hook)

        # print cls.module_hooks
        
    def add_hook(cls, module, hook):
        """ Add a hook named 'hook' for module 'module' """

        l = cls.module_hooks.get(module)
        if l is None:
            cls.module_hooks[module] = [hook]
        else:
            l.append(hook)

    def get_hooks(cls, module):
        """ Return all hooks for module 'module' """

        return cls.module_hooks.get(module)

    def get_all_hooks(cls):
        """ Return the hooks data structure """

        # Note this is a copy of the dictionary,
        # so modifying it will not have any impact
        # locally.
        return cls.module_hooks.copy()

    def set_hook_func(self, context, func):
        """ Set hook function 'func' for context 'context' """

        self.run_hooks[context] = func
        # Inject the given function in place of the original
        module, hook = context.split(':')
        # Load module and get the entry point
        M = __import__(module)
        orig_func = getattr(M, '__hooks__').get(hook)
        # Orig func is in the form class:function
        klassname, function = orig_func.split(':')
        if klassname:
            klass = getattr(M, klassname)
            # Replace function with the new one
            funcobj = getattr(klass, function)
            setattr(klass, function, func)
            # print getattr(klass, function)
        else:
            # No class perhaps. Directly override
            setattr(M, function, func)
            
    def get_hook_func(self, context):

        return self.run_hooks.get(context)

    def get_all_hook_funcs(self):

        return self.run_hooks.copy()

    add_all_hooks = classmethod(add_all_hooks)    
    add_hook = classmethod(add_hook)
    get_hooks = classmethod(get_hooks)
    get_all_hooks = classmethod(get_all_hooks)
    
HarvestManHooks.add_all_hooks()
              
def register_hook_function(context, func):
    """ Register function 'func' as
    a hook at context 'context' """
    
    # The context is a string of the form module:hook
    # Example => crawler:fetcher_process_url_hook

    # Hooks are defined in modules using the global dictionary
    # __hooks__. This module will load all hooks from modules
    # supporting hookable(pluggable) function definitions, when
    # this module is imported and add the hook definitions to
    # the class HarvestManHooks.
    
    # The function is a hook function/method object which is defined
    # at the time of calling this function. This function
    # will not attempt to validate whether the hook function exists
    # and whether it accepts the right parameters (if any). Any
    # such validation is done by the Python run-time. The function
    # can be a module-level, class-level or instance-level function.
    
    module, hook = context.split(':')

    Hook = HarvestManHooks.getInstance()
    
    # Validity checks...
    if module not in HarvestManHooks.get_all_hooks().keys():
        raise HarvestManHooksException,'Error: %s has no hooks defined!' % module

    # print HarvestManHooks.get_hooks(module)
    
    if hook not in HarvestManHooks.get_hooks(module):
        raise HarvestManHooksException,'Error: Hook %s is not defined for module %s!' % (hook, module)

    # Finally add hook..
    Hook.set_hook_func(context, func)
    

def myfunc():
    pass

if __name__ == "__main__":
    register_hook_function('datamgr:download_url_hook', myfunc)
    print HarvestManHooks.getInstance().get_all_hook_funcs()

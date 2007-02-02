""" Module allowing developer extensions to HarvestMan.
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

    supported_modules = ('crawler','havestman', 'urlqueue', 'datamgr', 'connector')
    module_hooks = {}
    
    def __init__(self):
        self.run_hooks = {}
        
    def add_hook(cls, module, hook):
        """ Add a hook named 'hook' for module 'module' """

        if module in cls.supported_modules:
            l = cls.module_hooks.get(module)
            if l is None:
                cls.module_hooks[module] = [hook]
            else:
                l.append(hook)
        else:
            raise HarvestManHooksException,'Error: Hooks are not supported for module %s!' % module

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

    def get_hook_func(self, context):

        return self.run_hooks.get(context)

    def get_all_hook_funcs(self):

        return self.run_hooks.copy()
    
    add_hook = classmethod(add_hook)
    get_hooks = classmethod(get_hooks)
    get_all_hooks = classmethod(get_all_hooks)
    
# Hook which can replace the entire process_url method of the HarvestManUrlFetcher objects
HarvestManHooks.add_hook('crawler', 'process_url_hook_fetcher')
# Hook which can replace the entire process_url method of the HarvestManUrlCrawler objects
HarvestManHooks.add_hook('crawler', 'process_url_hook_crawler')
# Hook which can replace the download action in datamgr
HarvestManHooks.add_hook('datamgr','download_url_hook')

              
def register_hook_function(context, func):
    """ Register function 'func' as
    a hook at context 'context' """
    
    # The context is a string of the form module:hook
    # Example => crawler:download_url_hook_fetcher

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

    if hook not in HarvestManHooks.get_hooks(module):
        raise HarvestManHooksException,'Error: Hook %s is not defined for module %s!' % (hook, module)

    # Finally add hook..
    Hook.set_hook_func(context, func)
    

def myfunc():
    pass

if __name__ == "__main__":
    register_hook_function('crawler:download_url_hook_fetcher', myfunc)
    print HarvestManHooks.getInstance().get_all_hook_funcs()

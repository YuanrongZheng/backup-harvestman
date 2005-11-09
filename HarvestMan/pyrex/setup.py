from distutils.core import setup
from distutils.extension import Extension
from Pyrex.Distutils import build_ext


if __name__=="__main__":
    import os
    
    modname = os.environ.get('MODULE','')
    if modname:
        setup(
            name = "PyrexTest",
            ext_modules=[ 
            Extension(modname, [modname + '.pyx'], libraries = [])
            ],
            cmdclass = {'build_ext': build_ext}
            )
    

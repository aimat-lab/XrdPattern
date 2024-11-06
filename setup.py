#!/usr/bin/env python
from glob import glob

from setuptools import setup, find_packages, Extension
from distutils.command.build import build

# -------------------------------------------

class CustomBuild(build):
    sub_commands = [('build_ext', build.has_ext_modules),
                    ('build_py', build.has_pure_modules),
                    ('build_clib', build.has_c_libraries),
                    ('build_scripts', build.has_scripts)]


with open('requirements.txt','r') as f:
    reqs = f.read().split('\n')

# noinspection PyTypeChecker
setup(name='xrdpattern',
      version='0.4.0',
      description='Python library for XrdPatterns including file import, file export and postprocessing functionalities',
      install_requires=reqs,
      long_description=("Python library for XrdPatterns including import from data files, "
                        "export as json file and postprocessing functionalities. The data file "
                        "import functionalities are built on C++ library xylib so beyond a standard "
                        "python install, this library also requires: "
                        "\n- A C++ compiler and standard library "
                        "\n- A C++ to python bridge (Swig)"),
      packages=find_packages(),
      author = 'Daniel Hollarek',
      author_email = 'daniel.hollarek@googlemail.com',
      license='LGPL2.1',
      url='https://github.com/aimat-lab/xrdpattern',
      ext_modules=[Extension('_xylib',
                             sources=[f for f in glob('xylib/*.cpp') if f != 'xylib_wrap.cpp'] + ['xylib.i'],
                             language='c++',
                             swig_opts=['-c++', '-modern', '-modernargs', '-py3'],
                             include_dirs=['.'],
                             libraries=[])],
      py_modules=['xylib'],
      cmdclass={'build': CustomBuild},
      package_data = {'xrdpattern.xrd.constants': ['*'],
                      'xrdpattern.parsing.examples': ['*', 'datafolder/*']}
)

import setuptools
from distutils.core import setup

setuptools.setup(
    name='mpiscan',
    version='0.1',
    author='Jean-Baptiste BESNARD',
    description='This is a tool to test and harvest results from MPI implementations.',
    entry_points = {
        'console_scripts': ['mpiscan=lib.mpiscan.mpiscan:cli_entry'],
    },
    packages=["lib.mpiscan"],
    install_requires=[
        'rich'
    ],
    python_requires='>=3.5'
)

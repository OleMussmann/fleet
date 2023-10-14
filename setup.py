from distutils.core import setup

setup(
    name='fleet',
    py_modules = ["commands.py", "colors.py"],
    version='0.0.1',
    scripts=['fleet.py',],
)

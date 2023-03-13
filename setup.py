from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(
    name='protomod',
    version='1.0.2',
    packages=['protomod'],
    license='MIT License',
    url='https://github.com/PouyaEsmaili/protomod',
    scripts=['scripts/protomod'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=['antlr4-python3-runtime==4.12.0'],
)
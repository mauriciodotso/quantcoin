from setuptools import find_packages, setup
from pip.req import parse_requirements

requirements = [str(ir.req) for ir in parse_requirements('requirements.txt', session="setuptools")]

setup(
    name="quantcoin",
    version="0.0.1-alpha",
    packages=find_packages(),
    install_requires=requirements
)

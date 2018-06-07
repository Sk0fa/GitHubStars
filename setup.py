from setuptools import setup


with open('README.md', 'r') as fr:
    long_description = fr.read()

setup(
    name='github_stars',
    version='1.0',
    author='Eganov Vladislav',
    author_email='vlad.eganov@gmail.com',
    description=("The utility for getting starred repos from github,"
                 " and getting the total count of stars for each repo"),
    long_description=long_description,
    packages=['github_stars'],
    package_dir={'github_stars': 'github_stars'},
    install_requires=['requests'],
)

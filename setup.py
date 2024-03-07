from setuptools import setup, find_packages

setup(
    name='cstlint',
    version='0.1.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'cstlint=cstlint.main:main',
        ],
    },
    # Add other package dependencies as needed
    install_requires=[
        'libcst',
        'click',  # If you are using click for your CLI
    ],
)


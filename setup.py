from setuptools import setup, find_packages

with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = f.read().split('\n')
    
setup(
    name='help learning korean',
    version='0.0.1', 
    install_requires=requirements,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'start=korean.__main__:main'
        ]
    }
)
from setuptools import setup

setup(name='mturkutils',
      version='0.1.0',
      description='Scripts for working with Amazon Mechanical Turk',
      long_description='A set of scripts that somewhat replicate the original MTurk command line tools',
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2.7',
      ],
      keywords='aws, mturk',
      url='https://bitbucket.org/hlplab/mturkutils',
      author='Andrew Watts',
      author_email='awatts2@ur.rochester.edu',
      license='MIT',
      packages=['mturkutils',],
      install_requires=[
          'boto',
          'unicodecsv',
          'ruamel.yaml',
          'six',
      ],
      include_package_data=True,
      zip_safe=False)

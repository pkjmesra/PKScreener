# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
# import atexit, os
import sys
import setuptools  # noqa
from distutils.core import setup
from src.classes import VERSION

__USERNAME__ = 'pkjmesra'

with open('README.md', 'r') as fh:
	long_description = fh.read()
with open('requirements.txt', 'r') as fh:
	install_requires = fh.read().splitlines()

SYS_MAJOR_VERSION = str(sys.version_info.major)
SYS_VERSION = SYS_MAJOR_VERSION + '.' +str(sys.version_info.minor)

WHEEL_NAME = 'pkscreener-'+VERSION+'-py'+SYS_MAJOR_VERSION+'-none-any.whl'
TAR_FILE = 'pkscreener-'+VERSION+'.tar.gz'
EGG_FILE = 'pkscreener-'+VERSION+'-py'+SYS_VERSION+'.egg'
DIST_FILES = [WHEEL_NAME, TAR_FILE, EGG_FILE]
DIST_DIR = 'dist/'

# def _post_build():
# 	if "bdist_wheel" in sys.argv:
# 		for count, filename in enumerate(os.listdir(DIST_DIR)):
# 			if filename in DIST_FILES:
# 				os.rename(DIST_DIR + filename, DIST_DIR + filename.replace('pkscreener-', 'pkscreener_'+__USERNAME__+'-'))

# atexit.register(_post_build)

setup(
	name = 'pkscreener',
	packages=setuptools.find_packages(where=".", exclude=["docs", "test"]),
	include_package_data = True,    # include everything in source control
	package_data={'src': ['pkscreener.ini']},
	# ...but exclude README.txt from all packages
	exclude_package_data = { '': ['*.yml'] },
	version = VERSION,
	description = 'A Python-based stock screener for NSE, India with alerts to Telegram Channel (pkscreener)',
	long_description = long_description,
	long_description_content_type="text/markdown",
	author = __USERNAME__,
	author_email = __USERNAME__+'@gmail.com',
	license = 'OSI Approved (MIT)',
	url = 'https://github.com/'+__USERNAME__+'/pkscreener', # use the URL to the github repo
	zip_safe=False,
	entry_points='''
	[console_scripts]
	pkscreener=pkscreener
	''',
	download_url = 'https://github.com/'+__USERNAME__+'/pkscreener/archive/v' + VERSION + '.zip',
	classifiers=[
	"License :: OSI Approved :: MIT License",
	"Operating System :: Windows, MacOS, Linux",
	'Programming Language :: Python',
	'Programming Language :: Python :: 3',
	'Programming Language :: Python :: 3.9',
	],
	install_requires = install_requires,
	keywords = ['NSE', 'Technical Indicators', 'Scanning','Stock Scanners'],
	test_suite="test",
),
python_requires='>=3.9',

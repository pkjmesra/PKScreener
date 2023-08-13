# -*- coding: utf-8 -*-
# """
#     The MIT License (MIT)

#     Copyright (c) 2023 pkjmesra

#     Permission is hereby granted, free of charge, to any person obtaining a copy
#     of this software and associated documentation files (the "Software"), to deal
#     in the Software without restriction, including without limitation the rights
#     to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#     copies of the Software, and to permit persons to whom the Software is
#     furnished to do so, subject to the following conditions:

#     The above copyright notice and this permission notice shall be included in all
#     copies or substantial portions of the Software.

#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#     IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#     FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#     AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#     LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#     OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#     SOFTWARE.

# """
"""
Spyder Editor

This is a temporary script file.

python setup.py clean build sdist bdist_wheel

"""
import sys
from distutils.core import setup

import setuptools  # noqa

from pkscreener.classes import VERSION

__USERNAME__ = "pkjmesra"
__PACKAGENAME__ = "pkscreener"
with open("README.md", "r") as fh:
    long_description = fh.read()
with open("requirements.txt", "r") as fh:
    install_requires = fh.read().splitlines()

SYS_MAJOR_VERSION = str(sys.version_info.major)
SYS_VERSION = SYS_MAJOR_VERSION + "." + str(sys.version_info.minor)

WHEEL_NAME = (
    __PACKAGENAME__ + "-" + VERSION + "-py" + SYS_MAJOR_VERSION + "-none-any.whl"
)
TAR_FILE = __PACKAGENAME__ + "-" + VERSION + ".tar.gz"
EGG_FILE = __PACKAGENAME__ + "-" + VERSION + "-py" + SYS_VERSION + ".egg"
DIST_FILES = [WHEEL_NAME, TAR_FILE, EGG_FILE]
DIST_DIR = "dist/"

# def _post_build():
# 	if "bdist_wheel" in sys.argv:
# 		for count, filename in enumerate(os.listdir(DIST_DIR)):
# 			if filename in DIST_FILES:
# 				os.rename(DIST_DIR + filename, DIST_DIR + filename.replace(__PACKAGENAME__+'-', __PACKAGENAME__+'_'+__USERNAME__+'-'))

# atexit.register(_post_build)

setup(
    name=__PACKAGENAME__,
    packages=setuptools.find_packages(where=".", exclude=["docs", "test"]),
    include_package_data=True,  # include everything in source control
    package_data={__PACKAGENAME__: [__PACKAGENAME__ + ".ini", 'courbd.ttf']},
    # ...but exclude README.txt from all packages
    exclude_package_data={"": ["*.yml"]},
    version=VERSION,
    description="A Python-based stock screener for NSE, India with alerts to Telegram Channel (pkscreener)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=__USERNAME__,
    author_email=__USERNAME__ + "@gmail.com",
    license="OSI Approved (MIT)",
    url="https://github.com/"
    + __USERNAME__
    + "/"
    + __PACKAGENAME__,  # use the URL to the github repo
    zip_safe=False,
    entry_points="""
	[console_scripts]
	pkscreener=pkscreener.pkscreenercli:pkscreenercli
	pkbot=pkscreener.pkscreenerbot:main
	""",
    download_url="https://github.com/"
    + __USERNAME__
    + "/"
    + __PACKAGENAME__
    + "/archive/v"
    + VERSION
    + ".zip",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    install_requires=install_requires,
    keywords=["NSE", "Technical Indicators", "Scanning", "Stock Scanners"],
    test_suite="test",
),
python_requires = (">=3.9",)

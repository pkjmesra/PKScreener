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
import platform
import subprocess
import sys
import os
import shutil
from distutils.core import setup

import setuptools  # noqa

try:
    from pkscreener.classes import VERSION
except:
    VERSION = "0.45"
    pass

__USERNAME__ = "pkjmesra"
__PACKAGENAME__ = "pkscreener"
install_requires=[]
if os.path.exists("README.md") and os.path.isfile("README.md"):
    with open("README.md", "r") as fh:
        long_description = fh.read()
if os.path.exists("requirements.txt") and os.path.isfile("requirements.txt"):
    with open("requirements.txt", "r") as fh:
        install_requires = fh.read().splitlines()
        install_requires.append("advanced_ta")
elif os.path.exists(os.path.join(__PACKAGENAME__,"requirements.txt")) and os.path.isfile(os.path.join(__PACKAGENAME__,"requirements.txt")):
    with open(os.path.join(__PACKAGENAME__,"requirements.txt"), "r") as fh:
        install_requires = fh.read().splitlines()
        install_requires.append("advanced_ta")

talibWindowsFile = ".github/dependencies/ta_lib-0.6.0-cp312-cp312-win_amd64.whl"
talibLinuxFile = ".github/dependencies/build_tools/github/talib.sh"
if "Windows" in platform.system() and os.path.isfile(talibWindowsFile) and os.path.isfile(talibWindowsFile):
    install_requires = [talibWindowsFile].extend(install_requires)
elif "Linux" in platform.system() and os.path.isfile(talibLinuxFile) and os.path.isfile(talibLinuxFile):
    subprocess.Popen(["chmod", "+x", talibLinuxFile])
    subprocess.Popen(talibLinuxFile, shell=True)
elif "Darwin" in platform.system():
    subprocess.Popen("brew install ta-lib && brew upgrade ta-lib", shell=True)
# For Darwin, brew install ta-lib will work

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
PYTHON_VERSION = (3, 12)

# def _post_build():
# 	if "bdist_wheel" in sys.argv:
# 		for count, filename in enumerate(os.listdir(DIST_DIR)):
# 			if filename in DIST_FILES:
# 				os.rename(DIST_DIR + filename, DIST_DIR + filename.replace(__PACKAGENAME__+'-', __PACKAGENAME__+'_'+__USERNAME__+'-'))

# atexit.register(_post_build)

try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
    class bdist_wheel(_bdist_wheel):
        def finalize_options(self):
            _bdist_wheel.finalize_options(self)
            self.root_is_pure = False
except ImportError:
    bdist_wheel = None

package_files_To_Install = ["LICENSE","README.md","requirements.txt",f"docs{os.sep}LICENSE-Others",
                            f"Disclaimer.txt",f"screenshots{os.sep}logos{os.sep}LogoWM.png"]
package_files = [__PACKAGENAME__ + ".ini","courbd.ttf"]
package_dir = os.path.join(os.getcwd(),__PACKAGENAME__)
if os.path.exists(package_dir):
    for file in package_files_To_Install:
        targetFileName = file.split(os.sep)[-1].split(".")[0] + ".txt"
        package_files.append(targetFileName)
        srcFile = os.path.join(os.getcwd(),file)
        if os.path.isfile(srcFile):
            shutil.copy(srcFile,os.path.join(package_dir,targetFileName))

setup(
    name=__PACKAGENAME__,
    packages=setuptools.find_packages(where=".", exclude=["docs", "test"]),
    cmdclass={'bdist_wheel': bdist_wheel},
    include_package_data=True,  # include everything in source control
    package_data={
        __PACKAGENAME__: package_files
    },
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
	pkbot=pkscreener.pkscreenerbot:runpkscreenerbot
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
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
    install_requires=install_requires,
    keywords=["NSE", "Technical Indicators", "Scanning", "Stock Scanners"],
),
python_requires = (">=3.12",)

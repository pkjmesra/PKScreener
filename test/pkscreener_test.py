'''
 *  Project             :   Screenipy
 *  Author              :   Pranjal Joshi
 *  Created             :   29/04/2021
 *  Description         :   Automated Test Script for pkscreener
'''
# pytest --cov --cov-report=html:coverage_re

import pytest
import sys
import os
import numpy as np
import pandas as pd
import configparser
import requests
import json
import platform
import shutil
try:
    shutil.copyfile('pkscreener/.env.dev', '.env.dev')
    sys.path.append(os.path.abspath('pkscreener'))
except:
    print('This test must be run from the root of the project!')
import pkscreener.classes.ConfigManager as ConfigManager
from pkscreener.classes import VERSION
from pkscreener.classes import Changelog
from pkscreener.classes.OtaUpdater import OTAUpdater
from pkscreener.classes.log import default_logger
import pkscreener.globals as globals
from pkscreener.globals import main
from pkscreener.pkscreenercli import *
from requests_cache import CachedSession
session = CachedSession('pkscreener_cache', cache_control=True)
last_release = 0
configManager = ConfigManager.tools()
configManager.default_logger = default_logger()
disableSysOut(input=False)

def cleanup():
    # configManager.deleteFileWithPattern(pattern='*.pkl')
    configManager.deleteFileWithPattern(pattern='*.png')
    configManager.deleteFileWithPattern(pattern='*.xlsx')

def test_if_changelog_version_changed():
    global last_release
    v = Changelog.changelog().split(']')[1].split('[')[-1]
    v = str(v).replace('v','')
    assert float(v) >= float(last_release)
    assert (f'v{str(last_release)}' in Changelog.changelog())
    assert (f'v{str(VERSION)}' in Changelog.changelog())

def test_if_release_version_increamented():
    global last_release
    r = session.get(
        "https://api.github.com/repos/pkjmesra/PKScreener/releases/latest",timeout=configManager.generalTimeout) #headers={'Connection': 'Close'})
    try:
        tag = r.json()['tag_name']
        version_components = tag.split('.')
        major_minor = '.'.join([version_components[0],version_components[1]])
        last_release = float(major_minor)
    except:
        if r.json()['message'] == 'Not Found':
            last_release = 0
    assert float(VERSION) >= last_release

def test_configManager():
    configManager.getConfig(ConfigManager.parser)
    assert configManager.duration is not None
    assert configManager.period is not None
    assert configManager.consolidationPercentage is not None

def test_option_E(mocker, capsys):
    try:
        mocker.patch('builtins.input', side_effect=['E', 
            str(configManager.period),
            str(configManager.daysToLookback),
            str(configManager.duration),
            str(configManager.minLTP),
            str(configManager.maxLTP),
            str(configManager.volumeRatio),
            str(configManager.consolidationPercentage),
            'y',
            'y',
        ])
        with pytest.raises((SystemExit, configparser.DuplicateSectionError)):
            main(testing=True,defaultConsoleAnswer='Y')
        out, err = capsys.readouterr()
        assert err == 0 or err == ''
    except StopIteration:
        pass

def test_option_H(mocker, capsys):
    try:
        mocker.patch('builtins.input', side_effect=['H'])
        # with pytest.raises((configparser.DuplicateSectionError)):
        main(testing=True, defaultConsoleAnswer='N')
        out, err = capsys.readouterr()
        assert err == ''
        assert (('ChangeLog' in out) and ('Home Page' in out)) 
    except StopIteration:
        pass

def test_nifty_prediction(mocker, capsys):
    try:
        mocker.patch('builtins.input', side_effect=['X', 'N'])
        main(testing=True)
        out, err = capsys.readouterr()
        assert err == ''
        assert 'Probability' in out
    except StopIteration:
        pass

def test_option_T(mocker, capsys):
    try:
        mocker.patch('builtins.input', side_effect=['T'])
        with pytest.raises((SystemExit, configparser.DuplicateSectionError)):
            main(testing=True,defaultConsoleAnswer='Y')
        out, err = capsys.readouterr()
        assert err == ''
        assert (('Configuration toggled' in out))
        # Revert to the original state
        mocker.patch('builtins.input', side_effect=['T'])
        with pytest.raises((SystemExit, configparser.DuplicateSectionError)):
            main(testing=True,defaultConsoleAnswer='Y')
        out, err = capsys.readouterr()
        assert err == ''
    except StopIteration:
        pass

def test_option_U(mocker, capsys):
    try:
        mocker.patch('builtins.input', side_effect=['U','Z','Y','\n'])
        # with pytest.raises(SystemExit):
        main(testing=True,startupoptions='U', defaultConsoleAnswer='N')
        out, err = capsys.readouterr()
        assert err == ''
    except StopIteration:
        pass

def test_option_X_0(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '0','0', globals.TEST_STKCODE, 'y'])
        main(testing=True,startupoptions='X:0:0:'+globals.TEST_STKCODE, defaultConsoleAnswer='Y')
        assert globals.screenResults is not None
        assert len(globals.screenResults) == 1 
    except StopIteration:
        pass

def test_option_X_1_0(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '0', 'y'])
        main(testing=True,startupoptions='X:1:0', defaultConsoleAnswer='Y')
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0 
    except StopIteration:
        pass

def test_option_X_1_1(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '1', 'y'])
        main(testing=True,startupoptions='X:1:1', defaultConsoleAnswer='Y')
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0 
    except StopIteration:
        pass

def test_option_X_1_2(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '2', 'y'])
        main(testing=True,startupoptions='X:1:2', defaultConsoleAnswer='Y')
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0 
    except StopIteration:
        pass

def test_option_X_1_3(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '3', 'y'])
        main(testing=True,startupoptions='X:1:3', defaultConsoleAnswer='Y')
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0 
    except StopIteration:
        pass

def test_option_X_1_4(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '4','5','y'])
        main(testing=True,startupoptions='X:1:4:5', defaultConsoleAnswer='Y')
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0 
    except StopIteration:
        pass

def test_option_X_1_5(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '5','10','90','y'])
        main(testing=True,startupoptions='X:1:5:10:90', defaultConsoleAnswer='Y')
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0 
    except StopIteration:
        pass

def test_option_X_1_6_1(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '6','1','y'])
        main(testing=True,startupoptions='X:1:6:1', defaultConsoleAnswer='Y')
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0 
    except StopIteration:
        pass

def test_option_X_1_6_2(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '6','2','y'])
        main(testing=True,startupoptions='X:1:6:2', defaultConsoleAnswer='Y')
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0 
    except StopIteration:
        pass

def test_option_X_1_6_3(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '6','3','y'])
        main(testing=True, startupoptions='X:1:6:3', defaultConsoleAnswer='Y')
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_1_6_4(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '6','4','50','y'])
        main(testing=True, startupoptions='X:1:6:4:50', defaultConsoleAnswer='Y')
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_1_6_6(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '6','6','4','y'])
        main(testing=True, startupoptions='X:1:6:6:4', defaultConsoleAnswer='Y')
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_1_9_3(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '9','3','y'])
        main(testing=True, startupoptions='X:1:9:3', defaultConsoleAnswer='Y')
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_1_11(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '11','y'])
        main(testing=True, startupoptions='X:1:11', defaultConsoleAnswer='Y')
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_Z(mocker, capsys):
    try:
        mocker.patch('builtins.input', side_effect=['X','Z',''])
        with pytest.raises(SystemExit):
            main(testing=True, startupoptions='X:Z', defaultConsoleAnswer='Y')
        out, err = capsys.readouterr()
        assert err == ''
    except StopIteration:
        pass

def test_option_X_12_1(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '12', '1','y'])
        main(testing=False, startupoptions='X:12:1', defaultConsoleAnswer='Y')
        assert globals.screenResults is not None
        assert globals.screenResultsCounter.value > 0
    except StopIteration:
        pass

def test_option_X_12_Z(mocker, capsys):
    try:
        mocker.patch('builtins.input', side_effect=['X','12','Z',''])
        with pytest.raises(SystemExit):
            main(testing=True, startupoptions='X:12:Z', defaultConsoleAnswer='Y')
        out, err = capsys.readouterr()
        assert err == ''
    except StopIteration:
        pass

def test_option_Z(mocker, capsys):
    try:
        mocker.patch('builtins.input', side_effect=['Z',''])
        with pytest.raises(SystemExit):
            main(testing=True, startupoptions='Z',defaultConsoleAnswer='Y')
        out, err = capsys.readouterr()
        assert err == ''
    except StopIteration:
        pass

def test_ota_updater():
    try:
        OTAUpdater.checkForUpdate(globals.proxyServer,VERSION,skipDownload=True)
        assert (
            "exe" in OTAUpdater.checkForUpdate.url or "bin" in OTAUpdater.checkForUpdate.url)
    except StopIteration:
        pass

def test_release_readme_urls():
    global last_release
    f = open('pkscreener/release.md', 'r')
    contents = f.read()
    f.close()
    failUrl = [f"https://github.com/pkjmesra/PKScreener/releases/download/{last_release}/pkscreenercli.bin",
               f"https://github.com/pkjmesra/PKScreener/releases/download/{last_release}/pkscreenercli.exe"]
    passUrl = [f"https://github.com/pkjmesra/PKScreener/releases/download/{VERSION}/pkscreenercli.bin",
               f"https://github.com/pkjmesra/PKScreener/releases/download/{VERSION}/pkscreenercli.exe"]
    if float(VERSION) > float(last_release):
        for url in failUrl:
            assert not url in contents
    for url in passUrl:
        assert url in contents

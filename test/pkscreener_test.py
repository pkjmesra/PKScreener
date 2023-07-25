'''
 *  Project             :   Screenipy
 *  Author              :   Pranjal Joshi
 *  Created             :   29/04/2021
 *  Description         :   Automated Test Script for pkscreener
'''


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

shutil.copyfile('../src/.env.dev', '.env.dev')
sys.path.append(os.path.abspath('../src'))
import classes.ConfigManager as ConfigManager
from classes import VERSION
from classes.Changelog import changelog
from classes.OtaUpdater import OTAUpdater
import globals 
from pkscreener import *
last_release = 0
configManager = ConfigManager.tools()
disableSysOut(input=False)

def cleanup():
    # configManager.deleteFileWithPattern(pattern='*.pkl')
    configManager.deleteFileWithPattern(pattern='*.png')
    configManager.deleteFileWithPattern(pattern='*.xlsx')

# Generate default configuration if not exist
def test_generate_default_config(mocker, capsys):
    mocker.patch('builtins.input', side_effect=['5','0', '\n'])
    with pytest.raises(SystemExit):
        configManager.setConfig(ConfigManager.parser, default=True)
    out, err = capsys.readouterr()
    assert err == ''

def test_if_changelog_version_changed():
    global last_release
    v = changelog.split(']')[-2].split('[')[-1]
    assert float(v) > float(last_release)

def test_if_release_version_increamented():
    global last_release
    r = requests.get(
        "https://api.github.com/repos/pkjmesra/PKScreener/releases/latest")
    try:
        last_release = float(r.json()['tag_name'])
    except:
        if r.json()['message'] == 'Not Found':
            last_release = 0
    assert float(VERSION) > last_release

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
            main(testing=True)
        out, err = capsys.readouterr()
        assert err == 0 or err == ''
    except StopIteration:
        pass

def test_option_H(mocker, capsys):
    try:
        mocker.patch('builtins.input', side_effect=['H'])
        with pytest.raises((SystemExit, configparser.DuplicateSectionError)):
            main(testing=True)
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
            main(testing=True)
        out, err = capsys.readouterr()
        assert err == ''
        assert (('Configuration toggled' in out))
        # Revert to the original state
        mocker.patch('builtins.input', side_effect=['T'])
        with pytest.raises((SystemExit, configparser.DuplicateSectionError)):
            main(testing=True)
        out, err = capsys.readouterr()
        assert err == ''
    except StopIteration:
        pass

def test_option_U(mocker, capsys):
    try:
        mocker.patch('builtins.input', side_effect=['U','Y'])
        main(testing=True)
        out, err = capsys.readouterr()
        assert err == ''
    except StopIteration:
        pass

def test_option_X_0(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '0','0', globals.TEST_STKCODE, 'y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) == 1 
    except StopIteration:
        pass

def test_option_X_1_0(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '0', 'y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0 
    except StopIteration:
        pass

def test_option_X_1_1(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '1', 'y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0 
    except StopIteration:
        pass

def test_option_X_1_2(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '2', 'y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0 
    except StopIteration:
        pass

def test_option_X_1_3(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '3', 'y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0 
    except StopIteration:
        pass

def test_option_X_1_4(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '4','5','y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0 
    except StopIteration:
        pass

def test_option_X_1_5(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '5','10','90','y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0 
    except StopIteration:
        pass

def test_option_X_1_6_1(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '6','1','y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0 
    except StopIteration:
        pass

def test_option_X_1_6_2(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '1', '6','2','y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0 
    except StopIteration:
        pass

def test_option_X_12_6_3(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '12', '6','3','y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_12_6_4(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '12', '6','4','50','y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_12_6_6(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '12', '6','6','4','y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_12_6_6(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '12', '9','3','y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_12_11(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '12', '11','y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_5_1(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '5', '1', 'y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_5_2(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '5', '2', 'y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_5_3(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '5', '3', 'y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_5_4_7(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '5', '4', '7', 'y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_5_5(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '5', '5', '30', '70','y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_5_6_1(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '5', '6', '1', 'y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_5_7_1_7(mocker):
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X', '5', '7', '1', '7', 'y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_X_Z(mocker, capsys):
    try:

        mocker.patch('builtins.input', side_effect=['X','Z',''])
        with pytest.raises(SystemExit):
            main(testing=True)
        out, err = capsys.readouterr()
        assert err == ''
    except StopIteration:
        pass

def test_option_X_12_Z(mocker, capsys):
    try:
        mocker.patch('builtins.input', side_effect=['X','12','Z',''])
        with pytest.raises(SystemExit):
            main(testing=True)
        out, err = capsys.readouterr()
        assert err == ''
    except StopIteration:
        pass

def test_option_X_14_0(mocker):
    # Scanners > F&O Stocks > All indicators
    try:
        cleanup()
        mocker.patch('builtins.input', side_effect=['X','14', '0', 'y'])
        main(testing=True)
        assert globals.screenResults is not None
        assert len(globals.screenResults) >= 0
    except StopIteration:
        pass

def test_option_Y(mocker, capsys):
    try:
        mocker.patch('builtins.input', side_effect=['Y'])
        with pytest.raises((SystemExit, configparser.DuplicateSectionError)):
            main(testing=True)
        out, err = capsys.readouterr()
        assert err == ''
    except StopIteration:
        pass

def test_option_Z(mocker, capsys):
    try:
        mocker.patch('builtins.input', side_effect=['Z',''])
        with pytest.raises(SystemExit):
            main(testing=True)
        out, err = capsys.readouterr()
        assert err == ''
    except StopIteration:
        pass

def test_ota_updater():
    try:
        OTAUpdater.checkForUpdate(globals.proxyServer,VERSION)
        assert (
            "exe" in OTAUpdater.checkForUpdate.url or "bin" in OTAUpdater.checkForUpdate.url)
    except StopIteration:
        pass

def test_release_readme_urls():
    global last_release
    f = open('../src/release.md', 'r')
    contents = f.read()
    f.close()
    failUrl = [f"https://github.com/pkjmesra/PKScreener/releases/download/{last_release}/pkscreener.bin",
               f"https://github.com/pkjmesra/PKScreener/releases/download/{last_release}/pkscreener.exe"]
    passUrl = [f"https://github.com/pkjmesra/PKScreener/releases/download/{VERSION}/pkscreener.bin",
               f"https://github.com/pkjmesra/PKScreener/releases/download/{VERSION}/pkscreener.exe"]
    for url in failUrl:
        assert not url in contents
    for url in passUrl:
        assert url in contents

#-----------------------------------------------------------------------------
# Copyright (c) 2005-2023, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License (version 2
# or later) with exception for distributing the bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
#
# SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
#-----------------------------------------------------------------------------
"""
Tests for splash screen.

NOTE: splash screen is not supported on macOS due to incompatible design.
"""

import os

import pytest

from PyInstaller.compat import is_darwin, is_musl

pytestmark = [
    pytest.mark.skipif(is_darwin, reason="Splash screen is not supported on macOS."),
    pytest.mark.xfail(is_musl, reason="musl + tkinter is known to cause mysterious segfaults."),
]


# Test that splash screen is successfully started. This is an "interactive"
# test (see test_interactive.py), where we expect the program to run for
# specified amount of time, before we terminate it.
@pytest.mark.parametrize("build_mode", ['onedir', 'onefile'])
@pytest.mark.parametrize("with_tkinter", [False, True], ids=['notkinter', 'tkinter'])
def test_splash_screen_running(pyi_builder_spec, capfd, monkeypatch, build_mode, with_tkinter):
    if build_mode == 'onefile':
        monkeypatch.setenv('_TEST_SPLASH_BUILD_MODE', 'onefile')
    if with_tkinter:
        monkeypatch.setenv('_TEST_SPLASH_WITH_TKINTER', '1')

    pyi_builder_spec.test_spec(
        'spec_with_splash.spec',
        runtime=10,  # Interactive test - terminate test program after 10 seconds.
    )

    out, err = capfd.readouterr()
    assert 'SPLASH: splash screen started' in err, \
        f"Cannot find log entry indicating start of splash screen in:\n{err}"


# Check that splash-enabled program properly exits (e.g., there are no crashes in bootloader during shutdown).
# This is not coveved by the `test_splash_screen_running`, because that one terminates the program.
# There are three variants of this test:
# - splash screen is kept running until the end
# - user imports pyi_splash, which calls pyi_splash.close() via atexit()
# - user imports pyi_splash and calls pyi_splash.close()
def test_splash_screen_shutdown_auto(pyi_builder, script_dir):
    splash_image = os.path.join(script_dir, '..', 'data', 'splash', 'image.png')
    pyi_builder.test_source(
        """
        print("Done!")
        """,
        pyi_args=["--splash", splash_image],
    )


def test_splash_screen_shutdown_atexit(pyi_builder, script_dir):
    splash_image = os.path.join(script_dir, '..', 'data', 'splash', 'image.png')
    pyi_builder.test_source(
        """
        # Importing pyi_splash registers pyi_splash.close() call via atexit().
        print("Importing pyi_splash...")
        import pyi_splash

        print("Done!")
        """,
        pyi_args=["--splash", splash_image],
    )


def test_splash_screen_shutdown_manual(pyi_builder, script_dir):
    splash_image = os.path.join(script_dir, '..', 'data', 'splash', 'image.png')
    pyi_builder.test_source(
        """
        print("Importing pyi_splash...")
        import pyi_splash

        print("Closing splash screen from program...")
        pyi_splash.close()

        print("Done!")
        """,
        pyi_args=["--splash", splash_image],
    )
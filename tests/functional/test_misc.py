#-----------------------------------------------------------------------------
# Copyright (c) 2021, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License (version 2
# or later) with exception for distributing the bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
#
# SPDX-License-Identifier: (GPL-2.0-or-later WITH Bootloader-exception)
#-----------------------------------------------------------------------------

import os

# Directory with testing modules used in some tests.
_MODULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules')


# Test inspect.getmodule() on stack-frames obtained by inspect.stack(). Reproduces the issue reported by #5963 while
# expanding the test to cover a package and its submodule in addition to the __main__ module.
def test_inspect_getmodule_from_stackframes(pyi_builder):
    pathex = os.path.join(_MODULES_DIR, 'pyi_inspect_getmodule_from_stackframes')
    # NOTE: run_from_path MUST be True, otherwise cwd + rel_path coincides with sys._MEIPASS + rel_path and masks the
    #       path resolving issue in onedir builds.
    pyi_builder.test_source(
        """
        import helper_package

        # helper_package.test_call_chain() calls eponymous function in helper_package.helper_module, which in turn uses
        # inspect.stack() and inspect.getmodule() to obtain list of modules involved in the chain call.
        modules = helper_package.test_call_chain()

        # Expected call chain
        expected_module_names = [
            'helper_package.helper_module',
            'helper_package',
            '__main__'
        ]

        # All modules must have been resolved
        assert not any(module is None for module in modules)

        # Verify module names
        module_names = [module.__name__ for module in modules]
        assert module_names == expected_module_names
        """,
        pyi_args=['--paths', pathex],
        run_from_path=True
    )


# Test whether dis can disassemble the __main__ module, as per #5897.
def test_dis_main(pyi_builder):
    pyi_builder.test_source(
        """
        import dis
        import sys

        print(dis.dis(sys.modules["__main__"].__loader__.get_code("__main__")))
        """
    )


# Test that single-file metadata (as commonly found in Debian/Ubuntu packages) is properly collected by copy_metadata().
def test_single_file_metadata(pyi_builder):
    # Add directory containing the my-test-package metadata to search path
    extra_path = os.path.join(_MODULES_DIR, "pyi_single_file_metadata")

    pyi_builder.test_source(
        """
        import pkg_resources

        # The pkg_resources.get_distribution() call automatically triggers collection of the metadata. While it does not
        # raise an error if metadata is not found while freezing, the calls below will fall at run-time in that case.
        dist = pkg_resources.get_distribution('my-test-package')

        # Sanity check
        assert dist.project_name == 'my-test-package'
        assert dist.version == '1.0'
        assert dist.egg_name() == f'my_test_package-{dist.version}-py{sys.version_info[0]}.{sys.version_info[1]}'
        """,
        pyi_args=['--paths', extra_path]
    )

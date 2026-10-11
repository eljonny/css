"""Unit tests module for the plist module"""

import tempfile
import unittest
from fnmatch import fnmatch
from os import close, unlink, walk
from pathlib import Path
from typing import ClassVar
from xml.parsers.expat import ExpatError

import pytest

from .plist import readPlist, writePlist


class TestPlist(unittest.TestCase):
  """Unit test class for: cs.app.osx.plist"""

  file = Path(__file__).resolve()
  TEST_DATA_DIR = f"{file.parents[5]}/lib_plist/test/data"
  EXCLUDE_FILES: ClassVar[list[str]] = [
    'invalid_tag.plist',
    'amp.plist',
    'malformed_dict.b_plist',
    'recursion.b_plist',
  ]

  def setUp(self):
    """Test setup."""
    self.test_files_bin = []
    self.test_files_xml = []
    self.test_neg_bin = []
    self.test_neg_xml = []
    for (dirpath, dirnames, filenames) in walk(self.TEST_DATA_DIR):
      for filename in filenames:
        if filename not in self.EXCLUDE_FILES:
          if fnmatch(filename, "*.plist"):
            self.test_files_xml.append(f"{dirpath}/{filename}")
          elif fnmatch(filename, "*.b_plist"):
            self.test_files_bin.append(f"{dirpath}/{filename}")
        elif fnmatch(filename, "*.plist"):
          self.test_neg_xml.append(f"{dirpath}/{filename}")
        elif fnmatch(filename, "*.b_plist"):
          self.test_neg_bin.append(f"{dirpath}/{filename}")
      break

  def tearDown(self):
    """Undo test setup."""

  def testReadPlist(self):
    """Tests for the plist module readPlist function.

    Verify that known-good plist files read without raising errors.
    """
    for xml_plist in self.test_files_xml:
      readPlist(xml_plist, binary=False)
      readPlist(xml_plist)

    for b_plist in self.test_files_bin:
      readPlist(b_plist, binary=True)

  def testBadReadPlist(self):
    """Tests for the plist module readPlist function.

    Verify that known-bad plist files raise errors when read.
    """
    for xml_plist in self.test_neg_xml:
      if Path(xml_plist).name in (
          'invalid_tag.plist',
          'amp.plist'):
        with pytest.raises(ExpatError):
          readPlist(xml_plist)
      else:
        readPlist(xml_plist)

    for b_plist in self.test_neg_bin:
      if Path(b_plist).name in (
          'malformed_dict.b_plist',
          'recursion.b_plist'):
        with pytest.raises(AttributeError):
          readPlist(b_plist, binary=True)
      else:
        readPlist(b_plist, binary=True)

  def testWritePlist(self):
    """Tests for the plist module writePlist function.

    Verify that known-good plist files read then write without raising
     errors.
    """
    for xml_plist in self.test_files_xml:
      plist = readPlist(xml_plist)

      tfd, tpath = tempfile.mkstemp()
      close(tfd)

      writePlist(plist, tpath, binary=False)
      writePlist(plist, f"{tpath}_default")
      writePlist(plist, f"{tpath}_bin", binary=True)

      unlink(tpath)
      unlink(f"{tpath}_default")
      unlink(f"{tpath}_bin")

import pytest
import tempfile
import unittest
from fnmatch import fnmatch
from os import close, unlink, walk
from pathlib import Path
from xml.parsers.expat import ExpatError

from .plist import readPlist, writePlist


class TestPlist(unittest.TestCase):
  ''' Unit tests for: cs.app.osx.plist
  '''

  file = Path(__file__).resolve()
  TEST_DATA_DIR = f"{file.parents[5]}/libplist/test/data"
  EXCLUDE_FILES = [
    'invalid_tag.plist',
    'amp.plist',
    'malformed_dict.bplist',
    'recursion.bplist',
  ]

  def setUp(self):
    ''' Test setup.
    '''
    self.test_files_bin = []
    self.test_files_xml = []
    self.test_neg_bin = []
    self.test_neg_xml = []
    for (dirpath, dirnames, filenames) in walk(self.TEST_DATA_DIR):
      for filename in filenames:
        if filename not in self.EXCLUDE_FILES:
          if fnmatch(filename, "*.plist"):
            self.test_files_xml.append(f"{dirpath}/{filename}")
          elif fnmatch(filename, "*.bplist"):
            self.test_files_bin.append(f"{dirpath}/{filename}")
        else:
          if fnmatch(filename, "*.plist"):
            self.test_neg_xml.append(f"{dirpath}/{filename}")
          elif fnmatch(filename, "*.bplist"):
            self.test_neg_bin.append(f"{dirpath}/{filename}")
      break

  def tearDown(self):
    ''' Undo test setup.
    '''

  def testReadPlist(self):
    for xmlPlist in self.test_files_xml:
      readPlist(xmlPlist, binary=False)
      readPlist(xmlPlist)

    for bPlist in self.test_files_bin:
      readPlist(bPlist, binary=True)

  def testBadReadPlist(self):
    for xmlPlist in self.test_neg_xml:
      if Path(xmlPlist).name in (
          'invalid_tag.plist',
          'amp.plist'):
        with pytest.raises(ExpatError):
          readPlist(xmlPlist)
      else:
        readPlist(xmlPlist)

    for bPlist in self.test_neg_bin:
      if Path(bPlist).name in (
          'malformed_dict.bplist',
          'recursion.bplist'):
        with pytest.raises(AttributeError):
          readPlist(bPlist, binary=True)
      else:
        readPlist(bPlist, binary=True)

  def testWritePlist(self):
    for xmlPlist in self.test_files_xml:
      plist = readPlist(xmlPlist)

      tfd, tpath = tempfile.mkstemp()
      close(tfd)

      writePlist(plist, tpath, binary=False)
      writePlist(plist, f"{tpath}_default")
      writePlist(plist, f"{tpath}_bin", binary=True)

      unlink(tpath)
      unlink(f"{tpath}_default")
      unlink(f"{tpath}_bin")

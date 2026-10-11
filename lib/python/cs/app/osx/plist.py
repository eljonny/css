#!/usr/bin/python
#

"""Some simple Apple plist facilities.

Supports binary plist files, which the stdlib `plistlib` module has
issues with.
"""

import base64
import os
import plistlib
import subprocess
import tempfile
from datetime import datetime, timezone

from plist import FMT_BINARY, FMT_XML, dump, load, loads

from cs.logutils import warning
from cs.pfx import Pfx

try:
  from lxml import etree
except ImportError:
  import xml.etree.ElementTree as etree

__version__ = '20260816'

# Add flake8 fixes - easy fixes -
# Convert readPlist and writePlist to using libplist Cython bindings
#  (2026-08-16) -
# Jonathan Hyry <jonathan.hyry@outlook.com> - 2026-03-29

DISTINFO = {
  'keywords': ["python3"],
  'classifiers': [
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
  ],
  'install_requires': [
    'cs.logutils',
    'cs.pfx'
  ],
}


def import_as_etree(plist):
  """Load an Apple plist and return an etree.Element.

  .. ATTENTION::
    This function depends on Apple `plutil` CLI utility.

  Paramaters:
  * `plist`: the source plist: data if `bytes`, filename if `str`,
    otherwise a file object open for binary read.
  """
  if isinstance(plist, bytes):
    # read bytes as a data stream
    # write to temp file, decode using plutil
    with tempfile.NamedTemporaryFile() as tfp:
      tfp.write(plist)
      tfp.flush()
      tfp.seek(0, 0)
      return import_as_etree(tfp.file)
  if isinstance(plist, str):
    # presume plist is a filename
    with open(plist, "rb") as pfp:
      return import_as_etree(pfp)
  # presume plist is a file
  with subprocess.Popen(['plutil', '-convert', 'xml1', '-o', '-', '-'],
                        stdin=plist, stdout=subprocess.PIPE) \
      as p_plutil:
    plutil_stdout = etree.parse(p_plutil.stdout)
    retcode = p_plutil.wait()
  if retcode != 0:
    raise ValueError(' '.join([
      f"export_xml_as_plist(E={plutil_stdout},...): plutil exited ",
      f"with returncode={retcode}"
    ]))
  return plutil_stdout


def ingest_plist(plist, recurse=False, resolve=False):  # noqa: D417
  """Ingest an Apple plist and return as a `PListDict`.

  Trivial wrapper for `import_as_etree` and `ingest_plist_etree`.

  Parameters
  ----------
  * `plist`: the source plist: data if `bytes`, filename if `str`,
    otherwise a file object open for binary read.
  * `recurse`: unpack any `bytes` objects as plists
  * `resolve`: resolve unpacked `bytes` plists' `'$objects'` entries

  """
  if resolve and not recurse:
    raise ValueError("resolve true but recurse false")
  with Pfx("ingest_plist(%r)", plist):
    pd = ingest_plist_etree(import_as_etree(plist))
    if recurse:
      for key, value in list(pd.items()):
        with Pfx("[%r]", key):
          if isinstance(value, bytes):
            subpd = ingest_plist(value)
            if resolve:
              subpd = resolve_object(subpd['$objects'], 1)
            pd[key] = subpd
    return pd


def export_xml_to_plist(e_tree, fp=None, fmt='binary1'):  # noqa: D417
  """Export the content of an `etree.Element` to a plist file.

  .. ATTENTION::
    This function depends on Apple `plutil` CLI utility.

  Parameters
  ----------
  * `e_tree`: the source `etree.Element`.
  * `fp`: the output file or filename (if a str).
  * `fmt`: the output format, default `"binary1"`.
    The format must be a valid value for the `-convert` option of
    plutil(1).

  """
  if isinstance(fp, str):
    with open(fp, "wb") as ofp:
      return export_xml_to_plist(e_tree, ofp, fmt=fmt)
  with subprocess.Popen(['plutil', '-convert', fmt, '-o', '-', '-'],
                        stdin=subprocess.PIPE, stdout=fp) as p_plutil:
    p_plutil.stdin.write(etree.tostring(e_tree))
    p_plutil.stdin.close()
    retcode = p_plutil.wait()
  if retcode != 0:
    raise ValueError(' '.join([
      f"export_xml_as_plist(E={e_tree},...): plutil exited with ",
      f"returncode={retcode}"
    ]))
  return None


def ingest_plist_etree(plist_etree):
  """Recursively load a plist's `ElementTree` into a Python structure.

  This returns a `PListDict`, a mapping of the plists's top dict
  with attribute access to key values.
  """
  root = plist_etree.getroot()
  if root.tag != 'plist':
    raise ValueError(f"{root} root Element is not a plist")
  return ingest_plist_dict(root[0])


# pylint: disable=too-many-return-statements
def ingest_plist_elem(e):  # noqa: PLR0911
  """Ingest a plist `Element`, converting types to Python objects.

  Unhandled types remain as the original `Element`.
  """
  if e.tag == 'dict':
    return ingest_plist_dict(e)
  if e.tag == 'array':
    return ingest_plist_array(e)
  if e.tag in ('string', 'key'):
    return e.text
  if e.tag == 'integer':
    return int(e.text)
  if e.tag == 'real':
    return float(e.text)
  if e.tag == 'false':
    return False
  if e.tag == 'true':
    return True
  if e.tag == 'data':
    return base64.b64decode(e.text)
  if e.tag == 'date':
    dt = datetime.strptime(e.text, '%Y-%m-%dT%H:%M:%SZ')  # noqa: DTZ007
    dt = datetime.combine(dt.date(), dt.time(), timezone.utc)
    return dt
  return e


def ingest_plist_array(pa):
  """Ingest a plist <array>, returning a Python list."""
  if pa.tag != 'array':
    raise ValueError(f"not an <array>: {pa}")
  a = []
  for i, e in enumerate(pa):
    e_i_obj = e
    a.append(ingest_plist_elem(e_i_obj))
  return a


def ingest_plist_dict(pd):
  """Ingest a plist <dict> Element, returning a PListDict."""
  if pd.tag != 'dict':
    raise ValueError(f"not a <dict>: {pd}")
  d = PListDict()
  key = None
  for i, e in enumerate(pd):
    if i % 2 == 0:
      if e.tag == 'key':
        key = e.text
      else:
        raise ValueError(f"unexpected key element {e}")
    else:
      value = ingest_plist_elem(e)
      d[key] = value
      key = None
  if key is not None:
    raise ValueError(f"no value for key {key}")
  return d


class PListDict(dict):
  """A mapping for a plist.

  Subclassing `dict`, which also allows access to the elements by
  attribute if that does not conflict with a `dict` method.
  """

  def __getattr__(self, attr):  # noqa: D105
    if attr[0].isalpha():
      try:
        return self[attr]
      except KeyError:
        # pylint: disable=raise-missing-from
        raise AttributeError(attr)
    raise AttributeError(attr)

  def __setattr__(self, attr, value):  # noqa: D105
    if attr in self:
      self[attr] = value
    else:
      super().__setattr__(attr, value)


# pylint: disable=too-many-statements.too-many-branches,too-many-nested-blocks,too-many-locals
def resolve_object(objs, i):  # noqa: C901,PLR0912,PLR0915
  """Resolve an object definition from structures.

  Structures like an iPhoto album queryData object list.
  """
  o = objs[i]
  if isinstance(o, (
      str, int, bool, float,
      ObjectClassDefinition,
      ObjectClassInstance)
  ):
    return o
  if isinstance(o, PListDict):
    if '$class' in o:
      # instance definition
      class_id = o.pop('$class')['CF$UID']
      class_def = resolve_object(objs, class_id)
      if 'NS.string' in o:
        # NS.string => flat string
        value = o.pop('NS.string')
      elif 'NS.objects' in o:
        objects = []
        for od in o.pop('NS.objects'):
          obj_id = od.pop('CF$UID')
          if od:
            raise ValueError(f"other fields in obj ref: {od}")
          objects.append(resolve_object(objs, obj_id))
        if 'NS.keys' in o:
          keys = []
          for kd in o.pop('NS.keys'):
            key_id = kd.pop('CF$UID')
            if kd:
              raise ValueError(f"other fields in key ref: {kd}")
            key = resolve_object(objs, key_id)
            keys.append(key)
          value = dict(zip(keys, objects))
        else:
          value = list(objects)
      elif 'NS.data' in o:
        value = o['NS.data']
      elif 'NSLocation' in o:
        count = o['NSRangeCount']
        value = o
      elif 'NSRangeData' in o:
        count = o['NSRangeCount']
        data = o['NSRangeData']
        key_id = data.pop('CF$UID')
        if data:
          raise ValueError(f"other fields in NSRangeData: {data}")
        data = resolve_object(objs, key_id)
        value = {'NSRangeCount': count, 'NSRangeData': data}
      elif 'data' in o:
        data = o['data']
        key_id = data.pop('CF$UID')
        if data:
          raise ValueError(f"other fields in data: {data}")
        data = resolve_object(objs, key_id)
        o['data'] = data
        value = data
      else:
        warning(f"unhandled $class instance: {o}")
      o = ObjectClassInstance(class_def, value)
    elif '$classname' in o:
      class_name = o.pop('$classname')
      class_mro = o.pop('$classes')
      o = ObjectClassDefinition(class_name, class_mro)
    else:
      warning(f"unknown dict content: {o}")
  else:
    warning(f"unsupported value {o}")
  objs[i] = o
  return o


# pylint: disable=too-few-public-methods
class ObjectClassDefinition:
  """A representation of a "class" object

  Used in `resolve_object()` for otherwise unrecognised objects which
  contain a `$classname` member.
  """

  def __init__(self, name, mro):  # noqa: D107
    self.name = name
    self.mro = mro

  def __str__(self):  # noqa: D105
    return f"{self.name}{self.mro}"

  __repr__ = __str__


class ObjectClassInstance:
  """A representation of a "class instance"

  Used in `resolve_object()` for objects with a `$class` member.
  """

  def __init__(self, class_def, value):  # noqa: D107
    self.class_def = class_def
    self.value = value

  @property
  def name(self):
    """The name from teh class definiton."""
    return self.class_def.name

  def __str__(self):  # noqa: D105
    return f"{self.name}{self.value}"

  __repr__ = __str__

  def __len__(self):  # noqa: D105
    return len(self.value)

  def __getitem__(self, key):  # noqa: D105
    return self.value[key]

  def __setitem__(self, key, value):  # noqa: D105
    self.value[key] = value

  def __contains__(self, key):  # noqa: D105
    return key in self.value

  def __getattr__(self, attr):  # noqa: D105
    try:
      return self.value[attr]
    except KeyError:
      # pylint: disable=raise-missing-from
      raise AttributeError(f"not in self.value: {attr}")
    except TypeError:
      # pylint: disable=raise-missing-from
      raise AttributeError(f"cannot index self.value: {attr}")
    raise AttributeError(attr)

  # pylint: disable=missing-function-docstring
  def keys(self):  # noqa: D102
    return self.value.keys()

  # pylint: disable=missing-function-docstring
  def items(self):  # noqa: D102
    return self.value.items()

  # pylint: disable=missing-function-docstring
  def values(self):  # noqa: D102
    return self.value.values()


def readPlist(path, binary=False, force_libplist=False):
  """Read a plist from a file path into a stdlib plistlib object.

  This function reads a plist from a file path using stdlib plistlib
  for XML plists (by default) and libimobiledevice's libplist for
  binary plists, and should work with any known-valid Apple plist.
  Optionally, you can force it to use libplist if plistlib is not
  working correctly, as libplist supports Apple plist constructs that
  sometimes do not work with Expat.

  Args:
      path (str):
        A file system path to a file with well-formed plist data.
      binary (bool, optional):
        This tells the parser to interpret the plist as a binary plist.
        Forces usage of libplist because plistlib has issues with
        binary plists; in the Python stdlib documentation, support
        appears to be in Python versions as old as 3.4, but real-world
        support for data is unknown.
        Defaults to False.
      force_libplist (bool, optional):
        Forces reading plist data from the specified file using
        libplist, even if it is an XML plist.
        Defaults to False.

  Returns:
      Dynamic:
        In almost all cases, the underlying parsers appear to return a
        dictionary.
        It is a possibility it may be some sort of other value type, so
        make sure to take that into account.
        Unknown if this can return None; it would be good to ensure you
        handle the case that it does just in case.

  """
  if not binary:
    with open(path, 'rb') as path_file:
      if force_libplist:
        return load(path_file, fmt=FMT_XML)
      else:
        return plistlib.loads(path_file.read(), fmt=plistlib.FMT_XML)

  tfd, tpath = tempfile.mkstemp()
  os.close(tfd)

  with open(path, 'rb') as bplist:
    plist = load(bplist, fmt=FMT_BINARY)
    with open(tpath, 'w') as plist_out_fp:
      dump(plist, plist_out_fp, fmt=FMT_XML)

  with open(tpath, 'rb') as xmlplist:
    pl = plistlib.loads(xmlplist.read(), fmt=plistlib.FMT_XML)

  os.unlink(tpath)

  return pl


def writePlist(root_obj, path, binary=False, force_libplist=False):
  """Write a plist as XML or binary to a valid, writable file location.

  Args:
      root_obj (dictionary):
        The root of the plist object to write.
      path (str):
        A file system path to a file where well-formed plist data will
        be written.
      binary (bool, optional):
        This tells the parser to write the plist in binary plist
        format.
        Forces usage of libplist because plistlib has issues with
        binary plists; in the Python stdlib documentation, support
        appears to be in Python versions as old as 3.4, but real-world
        support for data is unknown.
        Defaults to False.
      force_libplist (bool, optional):
        Forces writing plist data to the specified file using libplist,
        even if the output plist format is XML.
        Defaults to False.

  Returns:
      None: Does not return anything.

  """
  if not binary:
    with open(path, 'wb') as path_file:
      if force_libplist:
        dump(root_obj, path_file, fmt=FMT_XML)
      else:
        plistlib.dump(root_obj, path_file, fmt=plistlib.FMT_XML)

  tfd, tpath = tempfile.mkstemp()
  os.close(tfd)

  with open(tpath, 'wb') as tpath_file:
    plistlib.dump(root_obj, tpath_file, fmt=plistlib.FMT_XML)

  with open(tpath, 'rb') as written_plist:
    plist = loads(written_plist.read(), fmt=FMT_XML)
    with open(path, 'wb') as bplist_writer:
      dump(plist, bplist_writer, fmt=FMT_BINARY)

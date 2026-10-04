"""
Tests for olefile
"""

from __future__ import print_function
import unittest

import os, sys
import io
from shutil import copy2

# Insert the olefile package relative to this test dir in the sys.path
# to make sure we test the right one, in case another olefile version
# is also installed in the main python path.
_thismodule_dir = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))
# print('_thismodule_dir = %r' % _thismodule_dir)
_parent_dir = os.path.normpath(os.path.join(_thismodule_dir, '..'))
# print('_parent_dir = %r' % _thirdparty_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

import olefile


class Test_isOleFile(unittest.TestCase):
    'Tests for the isOleFile function'

    def setUp(self):
        self.non_ole_file = u"tests/images/flower.jpg"
        self.ole_file = u"tests/images/test-ole-file.doc"

    def test_isOleFile_str_path_false(self):
        'Test isOleFile with a unicode filename of a non-OLE file'
        is_ole = olefile.isOleFile(filename=self.non_ole_file)
        self.assertFalse(is_ole)

    def test_isOleFile_str_path_true(self):
        'Test isOleFile with a unicode filename of an OLE file'
        is_ole = olefile.isOleFile(filename=self.ole_file)
        self.assertTrue(is_ole)

    def test_isOleFile_bytes_path_false(self):
        'Test isOleFile with a bytes filename of a non-OLE file'
        is_ole = olefile.isOleFile(filename=self.non_ole_file.encode('latin_1'))
        self.assertFalse(is_ole)

    def test_isOleFile_bytes_path_true(self):
        'Test isOleFile with a bytes filename of an OLE file'
        is_ole = olefile.isOleFile(filename=self.ole_file.encode('latin_1'))
        self.assertTrue(is_ole)

    def test_isOleFile_bytes_string_false(self):
        'Test isOleFile with contents of a non-OLE file in a bytes string as filename parameter'
        with open(self.non_ole_file, 'rb') as f:
            data = f.read()
        assert (len(data) >= olefile.MINIMAL_OLEFILE_SIZE)
        is_ole = olefile.isOleFile(filename=data)
        self.assertFalse(is_ole)

    def test_isOleFile_small_bytes_string_false(self):
        'Test isOleFile with contents of a small non-OLE file (<1536b) in a bytes string as filename parameter'
        data = b" " * 100
        # In this case, we expect a FileNotFoundError exception, because isOleFile treats filename as a path
        # due to issue #142
        if sys.version_info[0] < 3:
            # On Python 2.x, this case raises an IOError exception:
            expected_exception = IOError
        else:
            # On Python 3.x, this case raises a FileNotFoundError exception:
            expected_exception = FileNotFoundError
        with self.assertRaises(expected_exception):
            is_ole = olefile.isOleFile(filename=data)

    def test_isOleFile_bytes_string_true(self):
        'Test isOleFile with contents of an OLE file in a bytes string as filename parameter'
        with open(self.ole_file, 'rb') as f:
            data = f.read()
        assert(len(data) >= olefile.MINIMAL_OLEFILE_SIZE)
        is_ole = olefile.isOleFile(filename=data)
        self.assertTrue(is_ole)

    def test_isOleFile_bytes_data_false(self):
        'Test isOleFile with contents of a non-OLE file in a bytes string as data parameter'
        with open(self.non_ole_file, 'rb') as f:
            data = f.read()
        is_ole = olefile.isOleFile(data=data)
        self.assertFalse(is_ole)

    def test_isOleFile_bytes_data_true(self):
        'Test isOleFile with contents of an OLE file in a bytes string as data parameter'
        with open(self.ole_file, 'rb') as f:
            data = f.read()
        is_ole = olefile.isOleFile(data=data)
        self.assertTrue(is_ole)

    def test_isOleFile_small_bytes_data_false(self):
        'Test isOleFile with contents of a small non-OLE file (<1536b) in a bytes string as data parameter'
        data = b" " * 100
        is_ole = olefile.isOleFile(data=data)
        self.assertFalse(is_ole)

    def test_isOleFile_small_bytes_ole_magic_data_false(self):
        'Test isOleFile with contents of a small non-OLE file (<1536b) starting with OLE magic in a bytes string as data parameter'
        with open(self.ole_file, 'rb') as f:
            data = f.read(100)
        is_ole = olefile.isOleFile(data=data)
        self.assertFalse(is_ole)

    def test_isOleFile_file_false(self):
        'Test isOleFile with a non-OLE file object as filename parameter'
        with open(self.non_ole_file, 'rb') as f:
            is_ole = olefile.isOleFile(filename=f)
        self.assertFalse(is_ole)

    def test_isOleFile_file_true(self):
        'Test isOleFile with an OLE file object as filename parameter'
        with open(self.ole_file, 'rb') as f:
            is_ole = olefile.isOleFile(filename=f)
        self.assertTrue(is_ole)


class TestOleFileIO(unittest.TestCase):
    'Tests for the OleFileIO class'

    def setUp(self):
        self.non_ole_file = u"tests/images/flower.jpg"
        self.ole_file = u"tests/images/test-ole-file.doc"

    def test_context_manager(self):
        with olefile.OleFileIO(self.ole_file) as ole:
            exists = ole.exists('worddocument')
            self.assertTrue(exists)

    def test_exists_worddocument(self):
        ole = olefile.OleFileIO(self.ole_file)
        exists = ole.exists('worddocument')
        self.assertTrue(exists)
        ole.close()

    def test_exists_no_vba_macros(self):
        ole = olefile.OleFileIO(self.ole_file)
        exists = ole.exists('macros/vba')
        self.assertFalse(exists)
        ole.close()

    def test_get_type(self):
        ole = olefile.OleFileIO(self.ole_file)
        doc_type = ole.get_type('worddocument')
        self.assertEqual(doc_type, olefile.STGTY_STREAM)
        ole.close()

    def test_get_size(self):
        ole = olefile.OleFileIO(self.ole_file)
        size = ole.get_size('worddocument')
        self.assertGreater(size, 0)
        ole.close()

    def test_get_rootentry_name(self):
        ole = olefile.OleFileIO(self.ole_file)
        root = ole.get_rootentry_name()
        self.assertEqual(root, "Root Entry")
        ole.close()

    def test_meta(self):
        ole = olefile.OleFileIO(self.ole_file)
        meta = ole.get_metadata()
        self.assertEqual(meta.author, b"Laurence Ipsum")
        self.assertEqual(meta.num_pages, 1)
        ole.close()

    def test_minifat_writing(self):
        ole_file_copy = "tests/images/test-ole-file-copy.doc"
        minifat_stream_name = "\x01compobj"
        if os.path.isfile(ole_file_copy):
            os.remove(ole_file_copy)
        copy2(self.ole_file, ole_file_copy)

        ole = olefile.OleFileIO(ole_file_copy, write_mode = True)
        stream = ole.openstream(minifat_stream_name)
        self.assertTrue(stream.size < ole.minisectorcutoff)
        str_read = stream.read()
        self.assertTrue(len(str_read) == stream.size)
        self.assertTrue(str_read != b'\x00' * stream.size)
        stream.close()
        ole.write_stream(minifat_stream_name, b'\x00' * stream.size)
        ole.close()

        ole = olefile.OleFileIO(ole_file_copy)
        stream = ole.openstream(minifat_stream_name)
        self.assertTrue(stream.size < ole.minisectorcutoff)
        str_read_replaced = stream.read()
        self.assertTrue(len(str_read_replaced) == stream.size)
        self.assertTrue(str_read_replaced != str_read)
        self.assertTrue(str_read_replaced == b'\x00' * len(str_read))
        stream.close()
        ole.close()
        os.remove(ole_file_copy)

    def test_write_sect_too_large(self):
        'Test write_sect with data larger than a sector'
        # read OLE file in memory to avoid writing to disk
        with open(self.ole_file, 'rb') as f:
            file_in_memory = io.BytesIO(f.read())
        with olefile.OleFileIO(file_in_memory, write_mode=True) as ole:
            size = ole.sector_size + 1
            # Attempt to overwrite last sector (ole.nb_sect - 1) with data too large
            # it should raise ValueError:
            with self.assertRaises(ValueError):
                ole.write_sect(ole.nb_sect - 1, b"x" * size)


class FileHandleCloseTest(unittest.TestCase):
    """Test file handles are closed correctly."""

    def setUp(self):
        self.non_ole_file = "tests/images/flower.jpg"
        self.ole_file = "tests/images/test-ole-file.doc"

    def leaking_test_function(self):
        """Function that leaks an open OleFileIO."""
        ole = olefile.OleFileIO(self.ole_file)

    @unittest.skip('Cannot predict when __del__ is run, so cannot test that '
                   'it issues a warning')
    # requires python version 3.2 or higher
    def test_warning(self):
        """Test that warning is issued when ole file leaks open fp."""
        with self.assertWarns(olefile.OleFileIONotClosed):
            self.leaking_test_function()

    @unittest.skip('Cannot test attribute fp of OleFileIO instance that '
                   'failed to construct')
    def test_init_fail(self):
        """Test that file handle is closed if open() from __init__ fails."""
        ole = None
        try:
            ole = olefile.OleFileIO(self.non_ole_file)
            self.fail('Should have raised an exception')
        except Exception as exc:
            self.assertEqual(str(exc), 'not an OLE2 structured storage file')
            self.assertTrue(ole.fp.closed)   # ole is still None

    def test_context_manager(self):
        """Test that file handle is closed by context manager."""
        file_handle = None
        with olefile.OleFileIO(self.ole_file) as ole:
            file_handle = ole.fp
            self.assertFalse(file_handle.closed)
        self.assertTrue(file_handle.closed)

    def test_manual(self):
        """Test that simple manual close always closes self-created handle."""
        ole = olefile.OleFileIO(self.ole_file)
        self.assertFalse(ole.fp.closed)
        _ = ole.listdir()
        self.assertFalse(ole.fp.closed)
        ole.close()
        self.assertTrue(ole.fp.closed)

    # TODO: check if this test is still relevant
    # def test_fp_stays_open(self):
    #     """Test that fp is not automatically closed if provided by caller."""
    #     with open(self.ole_file, 'rb') as file_handle:
    #         self.assertFalse(file_handle.closed)
    #         with olefile.OleFileIO(file_handle) as ole:
    #             self.assertFalse(file_handle.closed)
    #             self.assertEqual(file_handle, ole.fp)
    #         # check that handle is still open, although ole is now closed
    #         self.assertFalse(file_handle.closed)
    #
    #         # do something with it
    #         file_handle.seek(0)
    #         self.assertTrue(olefile.isOleFile(file_handle))
    #
    #     # now should be closed
    #     self.assertTrue(file_handle.closed)


# --- helpers to build synthetic property set streams ([MS-OLEPS]) ----------

import struct
import uuid

from olefile import olefile as _olem


def _build_section(entries):
    """
    Build a property set section from a list of (pid, payload) tuples.
    Each payload is the raw bytes of the TypedPropertyValue (starting with
    the 4 bytes property type), or None for a dictionary entry (pid 0).
    """
    count = len(entries)
    offset = 8 + 8 * count
    table = b''
    body = b''
    for pid, payload in entries:
        table += struct.pack('<II', pid, offset)
        body += payload
        body += b'\x00' * ((-len(body)) % 4)
        offset = 8 + 8 * count + len(body)
    return struct.pack('<II', 8 + 8 * count + len(body), count) + table + body


def _build_property_stream(fmtid_guid, entries):
    """
    Build a complete property set stream containing a single section with
    the given FMTID (a GUID string) and section entries.
    """
    section = _build_section(entries)
    header = (b'\xfe\xff' + struct.pack('<H', 0) + struct.pack('<I', 10) +
              b'\x00' * 16 + struct.pack('<I', 1))
    table = uuid.UUID(fmtid_guid).bytes_le + struct.pack('<I', 48)
    return header + table + section


def _typed(vt, value_bytes):
    'Build a TypedPropertyValue payload for a scalar type'
    return struct.pack('<I', vt) + value_bytes


def _lpstr(text_bytes):
    'Build the value bytes of a CodePageString (VT_LPSTR/VT_BSTR)'
    return struct.pack('<I', len(text_bytes)) + text_bytes


def _lpwstr(text):
    'Build the value bytes of a UnicodeString (VT_LPWSTR)'
    raw = text.encode('utf-16-le') + b'\x00\x00'
    return struct.pack('<I', len(raw) // 2) + raw


def _dict_entry(names, codepage):
    """
    Build the payload of a dictionary entry (property id 0) from a list of
    (pid, name) tuples.
    """
    payload = struct.pack('<I', len(names))
    for pid, name in names:
        if codepage == 1200:
            raw = name.encode('utf-16-le') + b'\x00\x00'
            entry = struct.pack('<II', pid, len(raw) // 2) + raw
        else:
            raw = name.encode('utf-8') + b'\x00'
            entry = struct.pack('<II', pid, len(raw)) + raw
        payload += entry + b'\x00' * ((-len(entry)) % 4)
    return payload


class TestGetPropertySets(unittest.TestCase):
    'Tests for OleFileIO.get_property_sets and the typed property parser'

    def setUp(self):
        self.ole_file = u"tests/images/test-ole-file.doc"

    def _parse(self, fmtid, entries, **kwargs):
        'Parse a synthetic property set stream, return the OlePropertySet'
        data = _build_property_stream(fmtid, entries)
        ole = olefile.OleFileIO(self.ole_file)
        try:
            sets = ole._parse_property_set_stream(data, **kwargs)
        finally:
            ole.close()
        self.assertEqual(len(sets), 1)
        return sets[0]

    def test_get_property_sets_real_file(self):
        'Parse the standard property set streams of the test Word document'
        ole = olefile.OleFileIO(self.ole_file)
        try:
            sets = ole.get_property_sets()
        finally:
            ole.close()
        fmtids = sorted(pset.fmtid for pset in sets)
        self.assertEqual(fmtids, sorted([
            olefile.FMTID_SUMMARY_INFORMATION,
            olefile.FMTID_DOCSUM_INFORMATION]))
        for pset in sets:
            self.assertEqual(pset.codepage, 1252)
            if pset.fmtid == olefile.FMTID_SUMMARY_INFORMATION:
                self.assertEqual(pset.get(4).value, 'Laurence Ipsum')
                self.assertEqual(pset.get(4).vt, _olem.VT_LPSTR)
                self.assertEqual(pset.get(14).value, 1)  # num_pages
                self.assertEqual(pset.as_dict()[8], 'Laurence Ipsum')
                self.assertEqual(pset.get(18).value, 'Microsoft Office Word')
            else:
                self.assertEqual(pset.get(15).name, None)
                self.assertEqual(pset.get(15).value, '')
                # VT_VECTOR|VT_LPSTR and VT_VECTOR|VT_VARIANT:
                self.assertEqual(pset.get(13).value, [''])
                self.assertEqual(pset.get(12).value, ['Title', 1])

    def test_get_property_sets_filename(self):
        'Parse a single property set stream specified by its path'
        ole = olefile.OleFileIO(self.ole_file)
        try:
            sets = ole.get_property_sets('\x05SummaryInformation')
        finally:
            ole.close()
        self.assertEqual(len(sets), 1)
        self.assertEqual(sets[0].fmtid, olefile.FMTID_SUMMARY_INFORMATION)

    def test_user_defined_properties_utf8(self):
        'Custom properties with names dictionary and UTF-8 code page'
        fmtid = olefile.FMTID_USER_DEFINED_PROPERTIES
        entries = [
            (1, _typed(_olem.VT_I2, struct.pack('<H', 65001))),
            (0, _dict_entry([(2, u'项目编号'), (3, u'审批人')], 65001)),
            (2, _typed(_olem.VT_LPSTR,
                       _lpstr(u'PRJ-2024-001'.encode('utf-8') + b'\x00'))),
            (3, _typed(_olem.VT_LPSTR,
                       _lpstr(u'张三'.encode('utf-8') + b'\x00'))),
        ]
        pset = self._parse(fmtid, entries)
        self.assertEqual(pset.fmtid, fmtid)
        self.assertEqual(pset.codepage, 65001)
        self.assertEqual(pset.get(1).value, 65001)
        prop = pset.get(2)
        self.assertEqual(prop.name, u'项目编号')
        self.assertEqual(prop.value, u'PRJ-2024-001')
        self.assertEqual(prop.vt, _olem.VT_LPSTR)
        self.assertEqual(prop.vt_name, 'VT_LPSTR')
        self.assertEqual(pset.get_by_name(u'审批人').value, u'张三')
        self.assertEqual(pset.get_by_name(u'审批人').pid, 3)

    def test_user_defined_properties_unicode(self):
        'Custom properties in a Unicode property set (code page 1200)'
        fmtid = olefile.FMTID_USER_DEFINED_PROPERTIES
        entries = [
            (1, _typed(_olem.VT_I2, struct.pack('<H', 1200))),
            (0, _dict_entry([(2, u'项目编号')], 1200)),
            (2, _typed(_olem.VT_LPSTR,
                       _lpstr(u'项目A'.encode('utf-16-le') + b'\x00\x00'))),
            (3, _typed(_olem.VT_LPWSTR, _lpwstr(u'李四'))),
        ]
        pset = self._parse(fmtid, entries)
        self.assertEqual(pset.codepage, 1200)
        self.assertEqual(pset.get(2).name, u'项目编号')
        self.assertEqual(pset.get(2).value, u'项目A')
        self.assertEqual(pset.get(3).value, u'李四')

    def test_string_without_codepage_falls_back_to_bytes(self):
        'Without a code page property, strings keep the legacy behaviour'
        entries = [
            (2, _typed(_olem.VT_LPSTR, _lpstr(b'hello\x00'))),
        ]
        pset = self._parse(olefile.FMTID_USER_DEFINED_PROPERTIES, entries)
        self.assertEqual(pset.codepage, None)
        self.assertEqual(pset.get(2).value, b'hello')

    def test_vector_types(self):
        'VT_VECTOR values are returned as lists (elements without padding)'
        vec_lpstr = struct.pack('<I', 2)
        for text in (b'alpha\x00', b'beta\x00'):
            vec_lpstr += _lpstr(text)
        vec_variant = (struct.pack('<I', 2) +
                       _typed(_olem.VT_LPSTR, _lpstr(b'one\x00')) +
                       _typed(_olem.VT_I4, struct.pack('<i', 42)))
        entries = [
            (1, _typed(_olem.VT_I2, struct.pack('<H', 65001))),
            (2, _typed(_olem.VT_VECTOR | _olem.VT_LPSTR,
                       vec_lpstr)),
            (3, _typed(_olem.VT_VECTOR | _olem.VT_VARIANT,
                       vec_variant)),
        ]
        pset = self._parse(olefile.FMTID_USER_DEFINED_PROPERTIES, entries)
        self.assertEqual(pset.get(2).value, ['alpha', 'beta'])
        self.assertEqual(pset.get(2).vt,
                         _olem.VT_VECTOR | _olem.VT_LPSTR)
        self.assertEqual(pset.get(3).value, ['one', 42])

    def test_vt_cf(self):
        'VT_CF values are returned as OleClipboardData objects'
        # standard clipboard format (CF_DIB legacy marker -2):
        packet1 = struct.pack('<iI', -2, 4) + b'DIB!'
        # registered clipboard format name:
        packet2 = struct.pack('<i', 500) + b'MyFormat\x00' + \
            struct.pack('<I', 3) + b'xyz'
        entries = [
            (2, _typed(_olem.VT_CF,
                       struct.pack('<I', len(packet1)) + packet1)),
            (3, _typed(_olem.VT_CF,
                       struct.pack('<I', len(packet2)) + packet2)),
        ]
        pset = self._parse(olefile.FMTID_USER_DEFINED_PROPERTIES, entries)
        clip1 = pset.get(2).value
        self.assertIsInstance(clip1, olefile.OleClipboardData)
        self.assertEqual(clip1.format_id, -2)
        self.assertEqual(clip1.format_name, None)
        self.assertEqual(clip1.data, b'DIB!')
        clip2 = pset.get(3).value
        self.assertEqual(clip2.format_id, None)
        self.assertEqual(clip2.format_name, 'MyFormat')
        self.assertEqual(clip2.data, b'xyz')

    def test_unknown_vt_returns_raw_bytes(self):
        'Unknown property types are returned as raw bytes, no exception'
        entries = [
            (2, struct.pack('<I', 9999) + b'\x01\x02\x03\x04'),
            (3, _typed(_olem.VT_I4, struct.pack('<i', 7))),
        ]
        pset = self._parse(olefile.FMTID_USER_DEFINED_PROPERTIES, entries)
        prop = pset.get(2)
        self.assertEqual(prop.vt, 9999)
        self.assertEqual(prop.vt_name, 'UNKNOWN')
        self.assertIsInstance(prop.value, bytes)
        self.assertTrue(prop.value.startswith(struct.pack('<I', 9999)))
        # the other properties are still parsed:
        self.assertEqual(pset.get(3).value, 7)

    def test_scalar_types(self):
        'Various scalar types, including VT_DECIMAL and VT_FILETIME'
        import datetime
        import decimal
        filetime = 13041688500 * 10000000  # seconds -> 100ns periods
        entries = [
            (2, _typed(_olem.VT_I8,
                       struct.pack('<q', -5000000000))),
            (3, _typed(_olem.VT_UI8,
                       struct.pack('<Q', 2 ** 63))),
            (4, _typed(_olem.VT_R8, struct.pack('<d', 2.5))),
            (5, _typed(_olem.VT_CY, struct.pack('<q', 123450))),
            (6, _typed(_olem.VT_DECIMAL,
                       struct.pack('<HBBI', 0, 2, 0, 0) +
                       struct.pack('<Q', 12345) + b'\x00\x00')),
            (7, _typed(_olem.VT_BOOL, struct.pack('<H', 0xFFFF))),
            (8, _typed(_olem.VT_FILETIME,
                       struct.pack('<Q', filetime))),
        ]
        pset = self._parse(olefile.FMTID_USER_DEFINED_PROPERTIES, entries,
                           convert_time=True)
        self.assertEqual(pset.get(2).value, -5000000000)
        self.assertEqual(pset.get(3).value, 2 ** 63)
        self.assertEqual(pset.get(4).value, 2.5)
        self.assertEqual(pset.get(5).value, decimal.Decimal('12.345'))
        self.assertEqual(pset.get(6).value, decimal.Decimal('123.45'))
        self.assertEqual(pset.get(7).value, True)
        self.assertIsInstance(pset.get(8).value, datetime.datetime)


if __name__ == '__main__':
    unittest.main()

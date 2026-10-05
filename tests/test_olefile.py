"""
Tests for olefile
"""

from __future__ import print_function
import unittest

import os, sys
import io
import struct
import uuid
import datetime
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


def build_typed_value(vt, payload):
    """Build a TypedPropertyValue: type (4 bytes) + payload."""
    return struct.pack('<I', vt) + payload


def build_codepage_string(text, codepage):
    """Build a CodePageString payload (size + characters) for a codepage."""
    if codepage == 1200:
        raw = text.encode('utf-16-le') + b'\x00\x00'
    elif codepage == 65001:
        raw = text.encode('utf-8') + b'\x00'
    else:
        raw = text.encode('cp%d' % codepage) + b'\x00'
    return struct.pack('<I', len(raw)) + raw


def build_dictionary(entries):
    """Build a Dictionary (property names), names encoded in UTF-8."""
    data = struct.pack('<I', len(entries))
    for pid, name in entries:
        raw = name.encode('utf-8') + b'\x00'
        data += struct.pack('<II', pid, len(raw)) + raw
        # each dictionary entry is padded to a multiple of 4 bytes:
        data += b'\x00' * ((-len(raw)) % 4)
    return data


def build_section(properties):
    """Build a property set section from (pid, value_bytes) tuples."""
    prop_list = b''
    values = b''
    offset = 8 + 8 * len(properties)
    for pid, value_bytes in properties:
        prop_list += struct.pack('<II', pid, offset)
        values += value_bytes
        offset += len(value_bytes)
    section = struct.pack('<I', len(properties)) + prop_list + values
    return struct.pack('<I', len(section) + 4) + section


def build_property_set_stream(sections):
    """Build a property set stream from (fmtid, section_bytes) tuples."""
    header = (struct.pack('<HHI', 0xFFFE, 0, 0) + b'\x00' * 16 +
              struct.pack('<I', len(sections)))
    entries = b''
    body = b''
    offset = 28 + 20 * len(sections)
    for fmtid, section in sections:
        entries += uuid.UUID(fmtid).bytes_le + struct.pack('<I', offset)
        body += section
        offset += len(section)
    return header + entries + body


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


class TestPropertySets(unittest.TestCase):
    """Tests for the typed property set API (get_property_sets)."""

    def setUp(self):
        self.ole_file = "tests/images/test-ole-file.doc"

    def parse_synthetic(self, stream_bytes):
        """
        Parse a synthetic property set stream with the same parser instance
        used for real OLE files (a real valid OLE file is only used to create
        the parser instance).
        """
        ole = olefile.OleFileIO(self.ole_file)
        try:
            return ole._parse_property_set_stream(
                'synthetic', io.BytesIO(stream_bytes))
        finally:
            ole.close()

    def test_real_file_property_sets(self):
        """All standard property sets of a real file are listed by FMTID."""
        ole = olefile.OleFileIO(self.ole_file)
        prop_sets = ole.get_property_sets()
        ole.close()
        self.assertEqual(len(prop_sets), 2)
        by_fmtid = dict((prop_set.fmtid, prop_set) for prop_set in prop_sets)
        self.assertIn(olefile.FMTID_SUMMARY_INFORMATION, by_fmtid)
        self.assertIn(olefile.FMTID_DOCUMENT_SUMMARY_INFORMATION, by_fmtid)
        summary = by_fmtid[olefile.FMTID_SUMMARY_INFORMATION]
        self.assertEqual(summary.codepage, 1252)
        self.assertEqual(summary.stream_name, '\x05SummaryInformation')
        author = summary.get(4)
        self.assertEqual(author.name, 'author')
        self.assertEqual(author.property_type, olefile.VT_LPSTR)
        self.assertEqual(author.type_name, 'VT_LPSTR')
        # strings are decoded using the codepage of the property set:
        self.assertEqual(author.value, 'Laurence Ipsum')
        # getitem / get_value / KeyError:
        self.assertEqual(summary[4].value, 'Laurence Ipsum')
        self.assertEqual(summary.get_value(999, 'default'), 'default')
        with self.assertRaises(KeyError):
            summary[999]
        # vector properties of DocumentSummaryInformation:
        docsum = by_fmtid[olefile.FMTID_DOCUMENT_SUMMARY_INFORMATION]
        titles = docsum.get(13)
        self.assertEqual(titles.property_type,
                         olefile.VT_VECTOR | olefile.VT_LPSTR)
        self.assertEqual(titles.type_name, 'VT_VECTOR|VT_LPSTR')
        self.assertEqual(titles.value, [''])
        pairs = docsum.get(12)
        self.assertEqual(pairs.property_type,
                         olefile.VT_VECTOR | olefile.VT_VARIANT)
        self.assertEqual(pairs.value, ['Title', 1])

    def test_custom_properties(self):
        """Custom properties are read with their names and typed values."""
        vt = olefile
        properties = [
            # the dictionary has no type field, it is property pid 0:
            (0, build_dictionary([(2, u'项目编号'), (3, u'审批人')])),
            (1, build_typed_value(vt.VT_I2, struct.pack('<H', 65001))),
            (2, build_typed_value(
                vt.VT_LPSTR, build_codepage_string(u'PRJ-2026-001', 65001))),
            (3, build_typed_value(
                vt.VT_LPSTR, build_codepage_string(u'张三', 65001))),
        ]
        stream = build_property_set_stream([
            (olefile.FMTID_USER_DEFINED_PROPERTIES,
             build_section(properties)),
        ])
        prop_sets = self.parse_synthetic(stream)
        self.assertEqual(len(prop_sets), 1)
        prop_set = prop_sets[0]
        self.assertEqual(prop_set.fmtid,
                         olefile.FMTID_USER_DEFINED_PROPERTIES)
        self.assertEqual(prop_set.codepage, 65001)
        project = prop_set.get(2)
        self.assertEqual(project.pid, 2)
        self.assertEqual(project.name, u'项目编号')
        self.assertEqual(project.property_type, olefile.VT_LPSTR)
        self.assertEqual(project.value, u'PRJ-2026-001')
        approver = prop_set.get(3)
        self.assertEqual(approver.name, u'审批人')
        self.assertEqual(approver.value, u'张三')
        # the dictionary itself is exposed as property pid 0:
        self.assertEqual(prop_set.get(0).value,
                         {2: u'项目编号', 3: u'审批人'})

    def test_codepage_1200_utf16(self):
        """CodePageString in a UTF-16LE (1200) property set is decoded."""
        vt = olefile
        properties = [
            (1, build_typed_value(vt.VT_I2, struct.pack('<H', 1200))),
            (2, build_typed_value(
                vt.VT_LPSTR,
                build_codepage_string(u'项目编号-001', 1200))),
        ]
        stream = build_property_set_stream([
            (olefile.FMTID_USER_DEFINED_PROPERTIES,
             build_section(properties)),
        ])
        prop_set = self.parse_synthetic(stream)[0]
        self.assertEqual(prop_set.codepage, 1200)
        self.assertEqual(prop_set.get(2).value, u'项目编号-001')

    def test_missing_codepage_falls_back_to_bytes(self):
        """Without a codepage, strings keep the legacy bytes representation."""
        vt = olefile
        raw = b'AB\x00CD\x00'
        properties = [
            (2, build_typed_value(
                vt.VT_LPSTR, struct.pack('<I', len(raw)) + raw)),
        ]
        stream = build_property_set_stream([
            (olefile.FMTID_USER_DEFINED_PROPERTIES,
             build_section(properties)),
        ])
        prop_set = self.parse_synthetic(stream)[0]
        self.assertIsNone(prop_set.codepage)
        self.assertEqual(prop_set.get(2).value, b'ABCD')

    def test_vector_types(self):
        """VT_VECTOR properties are returned as lists of typed values."""
        vt = olefile
        vector_i4 = (struct.pack('<I', 3) +
                     struct.pack('<iii', 1, -2, 3))
        variant_elements = (
            build_typed_value(vt.VT_LPSTR,
                              build_codepage_string(u'标题', 65001)) +
            build_typed_value(vt.VT_I4, struct.pack('<i', 42)))
        vector_variant = struct.pack('<I', 2) + variant_elements
        properties = [
            (1, build_typed_value(vt.VT_I2, struct.pack('<H', 65001))),
            (2, build_typed_value(vt.VT_VECTOR | vt.VT_I4, vector_i4)),
            (3, build_typed_value(
                vt.VT_VECTOR | vt.VT_VARIANT, vector_variant)),
        ]
        stream = build_property_set_stream([
            (olefile.FMTID_USER_DEFINED_PROPERTIES,
             build_section(properties)),
        ])
        prop_set = self.parse_synthetic(stream)[0]
        self.assertEqual(prop_set.get(2).value, [1, -2, 3])
        self.assertEqual(prop_set.get(3).value, [u'标题', 42])

    def test_vt_cf(self):
        """VT_CF is returned as a deterministic dict."""
        vt = olefile
        cf_data = b'\x01\x02\x03'
        payload = struct.pack('<II', 4 + len(cf_data), 2) + cf_data
        properties = [
            (1, build_typed_value(vt.VT_I2, struct.pack('<h', 1252))),
            (2, build_typed_value(vt.VT_CF, payload)),
        ]
        stream = build_property_set_stream([
            (olefile.FMTID_USER_DEFINED_PROPERTIES,
             build_section(properties)),
        ])
        prop_set = self.parse_synthetic(stream)[0]
        self.assertEqual(prop_set.get(2).property_type, olefile.VT_CF)
        self.assertEqual(prop_set.get(2).value,
                         {'format': 2, 'data': cf_data})

    def test_unknown_vt_returns_raw_bytes(self):
        """Unknown VT types yield raw bytes without raising any exception."""
        payload = b'\xde\xad\xbe\xef'
        properties = [
            (2, build_typed_value(0x0FFF, payload)),
        ]
        stream = build_property_set_stream([
            (olefile.FMTID_USER_DEFINED_PROPERTIES,
             build_section(properties)),
        ])
        prop_set = self.parse_synthetic(stream)[0]
        prop = prop_set.get(2)
        self.assertEqual(prop.property_type, 0x0FFF)
        self.assertEqual(prop.type_name, 'VT_UNKNOWN_4095')
        self.assertEqual(prop.value, payload)

    def test_scalar_and_special_types(self):
        """Integers, floats, bools, filetimes, CLSIDs and Unicode strings."""
        vt = olefile
        clsid_bytes = uuid.UUID(
            olefile.FMTID_USER_DEFINED_PROPERTIES).bytes_le
        properties = [
            (1, build_typed_value(vt.VT_I2, struct.pack('<H', 65001))),
            (2, build_typed_value(vt.VT_I8, struct.pack('<q', -5))),
            (3, build_typed_value(vt.VT_UI8, struct.pack('<Q', 1 << 63))),
            (4, build_typed_value(vt.VT_R8, struct.pack('<d', 1.5))),
            (5, build_typed_value(vt.VT_BOOL, struct.pack('<h', -1))),
            (6, build_typed_value(vt.VT_FILETIME,
                                  struct.pack('<Q', 130416885000000000))),
            (7, build_typed_value(vt.VT_CLSID, clsid_bytes)),
            (8, build_typed_value(
                vt.VT_LPWSTR,
                struct.pack('<I', 3) + u'你好'.encode('utf-16-le')
                + b'\x00\x00')),
        ]
        stream = build_property_set_stream([
            (olefile.FMTID_USER_DEFINED_PROPERTIES,
             build_section(properties)),
        ])
        prop_set = self.parse_synthetic(stream)[0]
        self.assertEqual(prop_set.get_value(2), -5)
        self.assertEqual(prop_set.get_value(3), 1 << 63)
        self.assertEqual(prop_set.get_value(4), 1.5)
        self.assertEqual(prop_set.get_value(5), True)
        self.assertEqual(prop_set.get_value(6),
                         datetime.datetime(2014, 4, 11, 11, 15))
        self.assertEqual(prop_set.get_value(7),
                         olefile.FMTID_USER_DEFINED_PROPERTIES)
        self.assertEqual(prop_set.get_value(8), u'你好')

    def test_multiple_sections_same_stream(self):
        """Custom properties live in a second section of the docsum stream."""
        vt = olefile
        docsum_section = build_section([
            (1, build_typed_value(vt.VT_I2, struct.pack('<h', 1252))),
            (15, build_typed_value(
                vt.VT_LPSTR, build_codepage_string(u'ACME', 1252))),
        ])
        custom_section = build_section([
            (0, build_dictionary([(2, u'项目编号')])),
            (1, build_typed_value(vt.VT_I2, struct.pack('<H', 65001))),
            (2, build_typed_value(
                vt.VT_LPSTR, build_codepage_string(u'X-1', 65001))),
        ])
        stream = build_property_set_stream([
            (olefile.FMTID_DOCUMENT_SUMMARY_INFORMATION, docsum_section),
            (olefile.FMTID_USER_DEFINED_PROPERTIES, custom_section),
        ])
        prop_sets = self.parse_synthetic(stream)
        self.assertEqual(len(prop_sets), 2)
        self.assertEqual(prop_sets[0].fmtid,
                         olefile.FMTID_DOCUMENT_SUMMARY_INFORMATION)
        self.assertEqual(prop_sets[0].get_value(15), u'ACME')
        self.assertEqual(prop_sets[1].fmtid,
                         olefile.FMTID_USER_DEFINED_PROPERTIES)
        self.assertEqual(prop_sets[1].get(2).name, u'项目编号')
        self.assertEqual(prop_sets[1].get_value(2), u'X-1')


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


if __name__ == '__main__':
    unittest.main()

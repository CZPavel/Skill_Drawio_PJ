from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from qa_office import qa_office

class OfficeProbeTests(unittest.TestCase):
    def test_missing_optional_library_is_unverified(self):
        with tempfile.TemporaryDirectory() as tmp:
            image=Path(tmp)/'source.png'; Image.new('RGB',(100,50),'white').save(image)
            before=image.read_bytes()
            with patch('qa_office.importlib.import_module',side_effect=ImportError):
                result=qa_office(image,Path(tmp)/'probe',render=True)
            self.assertEqual(result['status'],'unverified'); self.assertIsNone(result['artifact'])
            self.assertEqual(image.read_bytes(),before)
    def test_existing_probe_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            image=Path(tmp)/'source.png'; Image.new('RGB',(100,50)).save(image)
            probe=Path(tmp)/'diagram-probe.docx'; probe.write_bytes(b'original')
            with self.assertRaises(FileExistsError): qa_office(image,tmp)
            self.assertEqual(probe.read_bytes(),b'original')
    def test_available_libraries_create_targets_without_claiming_render(self):
        for target,dependency in [('document','docx'),('presentation','pptx')]:
            try: __import__(dependency)
            except ImportError: continue
            with self.subTest(target=target),tempfile.TemporaryDirectory() as tmp:
                image=Path(tmp)/'source.png'; Image.new('RGB',(100,50)).save(image)
                with patch('qa_office.shutil.which',return_value=None):
                    result=qa_office(image,Path(tmp)/'probe',target,render=True)
                self.assertTrue(Path(result['artifact']).is_file())
                self.assertEqual(result['status'],'unverified'); self.assertIsNone(result['rendered_pdf'])

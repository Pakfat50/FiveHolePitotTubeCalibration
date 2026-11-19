import ctypes
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import numpy as np

from c_export import export_c
from calibration import estimate


class TestCExport(unittest.TestCase):
    @unittest.skipUnless(shutil.which('cc'), 'C99 compiler required')
    def test_compile_and_estimate(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            model = np.arange(30).reshape(10, 3) / 7.3
            header = export_c(directory, model, 'cal_2f67.csv')
            common = directory / 'airdata.c'
            mtime = common.stat().st_mtime_ns
            self.assertEqual(header.name, 'cal_2f67.h')
            self.assertEqual(export_c(directory, model, 'cal_2f67.csv'), header)
            second = export_c(directory, model + 1, 'cal_2f67.csv')
            self.assertNotEqual(second, header)
            self.assertEqual(common.stat().st_mtime_ns, mtime)
            wrapper = directory / 'wrapper.c'
            wrapper.write_text(f'#include "{header.name}"\n#include "{second.name}"\n'
                               'int test(float a,float s,float t,AirDataResult *out) {\n'
                               '    return airdata_estimate(&cal_2f67,a,s,t,out);\n}\n')
            lib = directory / 'evaluate.so'
            subprocess.run(['cc','-std=c99','-pedantic-errors','-Werror','-fPIC','-shared',
                            str(common),str(wrapper),'-o',str(lib)],check=True)
            fn = ctypes.CDLL(str(lib)).test
            class Result(ctypes.Structure):
                _fields_ = [(k,ctypes.c_float) for k in ('alpha','beta','q')]
            fn.argtypes = [ctypes.c_float]*3+[ctypes.POINTER(Result)]
            out = Result()
            for total, aoa, aos in [(2.45,0,0),(15.3125,-1,3),(61.25,4,-9)]:
                self.assertTrue(fn(aoa,aos,total,ctypes.byref(out)))
                np.testing.assert_allclose((out.alpha,out.beta,out.q), estimate(model,total,aoa,aos),
                                           rtol=2e-6, atol=1e-6)
            previous = bytes(out)
            for aoa, aos, total in [(0,0,0),(1,2,-1),(np.nan,0,2),(0,np.inf,2)]:
                self.assertFalse(fn(aoa,aos,total,ctypes.byref(out)))
                self.assertEqual(bytes(out),previous)

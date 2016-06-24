#/usr/bin/python

import unittest

        
from cvmfsreplica.utils import date2seconds, check_disk_space


class TestDate2Seconds(unittest.TestCase):

    def test_date2seconds_edt(self):
        self.assertEqual(date2seconds("Fri Apr 15 11:32:19 EDT 2016"), 1460734339)
    def test_date2seconds_utc(self):
        self.assertEqual(date2seconds("Fri Apr 15 15:32:19 UTC 2016"), 1460734339)


class TestCheckDiskSpace(unittest.TestCase):

    def test_tmp_larger_0(self):
        self.assertTrue(check_disk_space('/tmp/', 0))
    def test_tmp_smaller(self):
        self.assertFalse(check_disk_space('/tmp/', 1000000000000000))



if __name__ == '__main__':
    unittest.main()


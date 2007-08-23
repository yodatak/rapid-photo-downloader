#!/usr/bin/env python
# -*- coding: latin1 -*-

### Copyright (C) 2007 Damon Lynch <damonlynch@gmail.com>

### This program is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; either version 2 of the License, or
### (at your option) any later version.

### This program is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.

### You should have received a copy of the GNU General Public License
### along with this program; if not, write to the Free Software
### Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import unittest

from renamesubfolderprefs import *

class PreferenceTest (unittest.TestCase):
    image_test = ( [TEXT, '', ''], 
                            [DATE_TIME, IMAGE_DATE, 'YYYYMMDD'],
                            [METADATA, APERTURE, ''],
                            [FILENAME, NAME_EXTENSION, UPPERCASE],
                )
    subfolder_test = ( [TEXT, '', ''], 
                                [DATE_TIME, IMAGE_DATE, 'HHMM'],
                                [METADATA, SHORT_CAMERA_MODEL_HYPHEN, 
                                 LOWERCASE],
                                [SEPARATOR, '', ''],
                                [FILENAME, EXTENSION, LOWERCASE]
                            )
                
    def testPrefImageList(self):
        for pref in self.image_test:
            result = checkPreferenceValid(DICT_IMAGE_RENAME_L0, pref)
            self.assertEqual(result, True)
            
    def testLargePrefList(self):
        prefList = []
        for pref in self.image_test:
            for l in pref:
                prefList.append(l)
                
        result = checkPreferenceValid(DICT_IMAGE_RENAME_L0, prefList)
        self.assertEqual(result, True)

    def testPrefSubfolderList(self):
        for pref in self.subfolder_test:
            result = checkPreferenceValid(DICT_SUBFOLDER_L0, pref)
            self.assertEqual(result, True)
    
    def testDateTimeL2Length(self):
        self.assertEqual(len(LIST_DATE_TIME_L2), len(DATE_TIME_CONVERT))
        
    def testDateTimeL2Conversion(self):
        self.assertEqual(convertDateForStrftime('YY'), '%y')
        

class BadPreferences(unittest.TestCase):
    bad_image_key = ( [1,2,3], 
                        [DATE_TIME.upper(), IMAGE_DATE, 'YYYYMMDD'],
                        [DATE_TIME, IMAGE_DATE.upper(), 'YYYYMMDD'],
                        [SEPARATOR, '', ''],
                        [None, None, None],
                    )
    bad_image_value = ( [DATE_TIME, TODAY, IMAGE_NUMBER_ALL],
                        [METADATA, CAMERA_MAKE, IMAGE_NUMBER_4],
                        [DATE_TIME, IMAGE_DATE, None],
                        [DATE_TIME, IMAGE_DATE, ''],
                        [DATE_TIME, None, None],
                        [DATE_TIME, '', ''],
                        )
                            
    bad_subfolder_key = ([FILENAME, NAME_EXTENSION, UPPERCASE],)
    bad_subfolder_value = ( [FILENAME, None, None],
                            [FILENAME, '', ''],)
    
    bad_length = ([], [DATE_TIME, TODAY], [DATE_TIME])
    
    bad_dt_conversion = ('HHYY', 'YYSS')
    
    bad_subfolder_combos = ([SEPARATOR, '', ''],
                            [FILENAME, NAME_EXTENSION, UPPERCASE, 
                                SEPARATOR, '', ''],
                            [FILENAME, NAME_EXTENSION, UPPERCASE, 
                                SEPARATOR, '', '',
                                SEPARATOR, '', '',
                                FILENAME, NAME_EXTENSION, UPPERCASE
                            ]
                            )
    
    def testBadImageKey(self):
        for pref in self.bad_image_key:
            self.assertRaises(PrefKeyError, checkPreferenceValid,
                                        DICT_IMAGE_RENAME_L0,
                                        pref)
            
    def testBadImageValue(self):
        for pref in self.bad_image_value:
            self.assertRaises(PrefValueInvalidError, checkPreferenceValid, 
                                        DICT_IMAGE_RENAME_L0, 
                                        pref)
                                        
    def testBadSubfolderKey(self):
        for pref in self.bad_subfolder_key:
            self.assertRaises(PrefKeyError, checkPreferenceValid, 
                                        DICT_SUBFOLDER_L0, 
                                        pref)

    def testBadSubfolderValue(self):
        for pref in self.bad_subfolder_value:
            self.assertRaises(PrefValueInvalidError, checkPreferenceValid, 
                                        DICT_SUBFOLDER_L0, 
                                        pref)
                                        
    def testBadLength(self):
        for pref in self.bad_length:
            self.assertRaises(PrefLengthError, checkPreferenceValid, 
                                        DICT_IMAGE_RENAME_L0,
                                        pref)
    def testBadDTConversion(self):
        for pref in self.bad_dt_conversion:
            self.assertRaises(PrefValueInvalidError, convertDateForStrftime, 
                                pref)
                                
    def testBadSubfolderCombo(self):
        
        for pref in self.bad_subfolder_combos:
            s = SubfolderPreferences(pref, self)
            self.assertRaises(PrefValueKeyComboError, s.checkPrefsForValidity)
            
if __name__ == "__main__":
    unittest.main() 

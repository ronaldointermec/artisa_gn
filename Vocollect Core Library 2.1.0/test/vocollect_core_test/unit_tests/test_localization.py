#
# Copyright (c) 2010 Vocollect, Inc.
# Pittsburgh, PA 15235
# All rights reserved.
#
# This source code contains confidential information that is owned by
# Vocollect, Inc. and may not be copied, disclosed or otherwise used without
# the express written consent of Vocollect, Inc.
#
import mock_catalyst
import unittest

from vocollect_core_test.base_test_case import BaseTestCaseCore #@UnusedImport - here for test framework
from vocollect_core.utilities import localization
from vocollect_core import itext


class Test(BaseTestCaseCore):

    def tearDown(self):
        super().tearDown()
        mock_catalyst.resource_files = {}
        mock_catalyst.manifest_contents = None
        localization._language_code = ''

    def test_itext(self):
        #Simulated preloaded files
        localization.load_prompts('en_us')
        values = {'v1' : 1, 'v2' : 2}
        
        #-------------------------------------------------------------------
        #tests when key is not defined that passed in key is used as resource
        
        #test standard python positional substitution 
        self.assertEquals(itext('value 1 = %(v2).2f%%, value 2 = %(v1).2f', values), 'value 1 = 2.00%, value 2 = 1.00')
        
        #test standard python substitution
        self.assertEquals(itext('value 1 = %.2f%%, value 2 = %.2f', 3, 4), 'value 1 = 3.00%, value 2 = 4.00')
        
        #test java style substitution
        self.assertEquals(itext('value 1 = {0}%%, value 2 = {1}', 5, 6), 'value 1 = 5%, value 2 = 6')
        
        
        #-------------------------------------------------------------------
        #tests when key is defined that correct resource is retrieved
        localization._resources['key1'] = 'value 1 = %(v2).2f%%, value 2 = %(v1).2f'
        localization._resources['key2'] = 'value 1 = %.2f%%, value 2 = %.2f'
        localization._resources['key3'] = 'value 1 = {0}%%, value 2 = {1}'
        
        values = {'v1' : 1, 'v2' : 2}
        
        #test standard python positional substitution 
        self.assertEquals(itext('key1', values), 'value 1 = 2.00%, value 2 = 1.00')
        
        #test standard python substitution
        self.assertEquals(itext('key2', 3, 4), 'value 1 = 3.00%, value 2 = 4.00')
        
        #test java style substitution
        self.assertEquals(itext('key3', 5, 6), 'value 1 = 5%, value 2 = 6')
        
        #-------------------------------------------------------------------
        #test error conditions key not found
        #key not found, so key is simply returned
        self.assertEquals(itext('key4', 7, 8), 'key4')
        
        #-------------------------------------------------------------------
        #Python Positional Error conditions

        #test dictionary not pass for python positional method, should get resource back 
        # with no substitutions
        self.assertEquals(itext('key1', 1, 2), 'value 1 = %(v2).2f%, value 2 = %(v1).2f')
        
        #Test value not found in dictionary, just get back resource
        values = {'v1' : 1}
        self.assertEquals(itext('key1', values), 'value 1 = %(v2).2f%, value 2 = %(v1).2f')
        
        #Test more values, should not cause error
        values = {'v1' : 1, 'v2' : 2, 'v3' : 3}
        self.assertEquals(itext('key1', values), 'value 1 = 2.00%, value 2 = 1.00')
        
        
        #-------------------------------------------------------------------
        #Python Non-Positional Error conditions

        #Test too few values passed, just get resource back 
        self.assertEquals(itext('key2', 1), 'value 1 = %.2f%, value 2 = %.2f')
        
        #Test too many values passed, just get resource back 
        self.assertEquals(itext('key2', 1, 2, 3), 'value 1 = %.2f%, value 2 = %.2f')
        
        
        #-------------------------------------------------------------------
        #Java Style Error conditions

        #Test too few values passed, get back with only values substituted that were provided 
        self.assertEquals(itext('key3', 1), 'value 1 = 1%, value 2 = {1}')
        
        #Test too many values passed, no an error, extra values ignored 
        self.assertEquals(itext('key3', 1, 2, 3), 'value 1 = 1%, value 2 = 2')
        
    def test_load_properties(self):
        
        #----------------------------------------------------------------------
        #Test normal load, and that more specific language code overrides 
        #less specific, and default (no language code)
        #dummy file is to test undefined files do not cause errors and are ignored
        mock_catalyst.manifest_contents = ('translations/test.properties|project|library\n' 
                                        'translations/test_en.properties|project|library\n'  
                                        'translations/test_en_us.properties|project|library\n'
                                        'translations/dummy_en_us.properties|project|library\n' 
                                       ) 
        
        mock_catalyst.resource_files['translations/test.properties'] = ('key1=test value 1\n'
                                                                     'key2=test value 2\n'
                                                                     'key3=test value 3\n')
        mock_catalyst.resource_files['translations/test_en.properties'] = ('key2=test value 2 en\n')
        mock_catalyst.resource_files['translations/test_en_us.properties'] = ('key3=test value 3 en_us\n')
        
        localization.load_prompts('en_US')
        self.assertEqual(itext('key1'), 'test value 1')
        self.assertEqual(itext('key2'), 'test value 2 en')
        self.assertEqual(itext('key3'), 'test value 3 en_us')
    
        #----------------------------------------------------------------------
        #test project files keys override library level keys
        mock_catalyst.manifest_contents += 'translations/project_en.properties|project\n'  
        mock_catalyst.resource_files['translations/project_en.properties'] = ('key4=test value 4 en project\n'
                                                                           'key2=test value 2 en project\n'
                                                                           'key3=test value 3 en project\n')
                                         
        localization.load_prompts('en_US')
        self.assertEqual(itext('key1'), 'test value 1')
        self.assertEqual(itext('key2'), 'test value 2 en project')
        self.assertEqual(itext('key3'), 'test value 3 en_us') #more specific code in library took priority
        self.assertEqual(itext('key4'), 'test value 4 en project')
    
        mock_catalyst.manifest_contents += 'translations/project_en_us.properties|project\n'  
        mock_catalyst.resource_files['translations/project_en_us.properties'] = ('key3=test value 3 en_us project\n')
                                         
        localization.load_prompts('en_US')
        self.assertEqual(itext('key1'), 'test value 1')
        self.assertEqual(itext('key2'), 'test value 2 en project')
        self.assertEqual(itext('key3'), 'test value 3 en_us project') 
        self.assertEqual(itext('key4'), 'test value 4 en project')

        #----------------------------------------------------------------------
        #test files read alphabetically when at same level (last one wins)
        
        mock_catalyst.manifest_contents += 'translations/c_file_en_us.properties|project\n'  
        mock_catalyst.resource_files['translations/c_file_en_us.properties'] = ('key4=test value 4 en_us c project\n')
                                         
        localization.load_prompts('en_US')
        self.assertEqual(itext('key4'), 'test value 4 en_us c project')

        #should not change anything, file c should still be read last
        mock_catalyst.manifest_contents += 'translations/a_file_en_us.properties|project\n'  
        mock_catalyst.resource_files['translations/a_file_en_us.properties'] = ('key4=test value 4 en_us a project\n')
        
        localization.load_prompts('en_US')
        self.assertEqual(itext('key4'), 'test value 4 en_us c project')
        
        #should now be read from file d
        mock_catalyst.manifest_contents += 'translations/d_file_en_us.properties|project\n'  
        mock_catalyst.resource_files['translations/d_file_en_us.properties'] = ('key4=test value 4 en_us d project\n')
        
        localization.load_prompts('en_US')
        self.assertEqual(itext('key4'), 'test value 4 en_us d project')
        
        #----------------------------------------------------------------------
        #test language is reloaded when language code changes
        mock_catalyst.manifest_contents += 'translations/c_file_fr_fr.properties|project\n'  
        mock_catalyst.resource_files['translations/c_file_fr_fr.properties'] = ('key4=test value 4 fr_fr c project\n')
        
        localization.load_prompts('fr_fr')
        #first ensure French was loaded, and English is gone, key4 should be only value, plus the default keys
        self.assertEqual(localization._resources['key1'], 'test value 1')
        self.assertEqual(localization._resources['key2'], 'test value 2')
        self.assertEqual(localization._resources['key3'], 'test value 3')
        self.assertEqual(localization._resources['key4'], 'test value 4 fr_fr c project')

        #check when itext is called, English should be reloaded
        self.assertEqual(itext('key1'), 'test value 1')
        self.assertEqual(itext('key2'), 'test value 2 en project')
        self.assertEqual(itext('key3'), 'test value 3 en_us project')
        self.assertEqual(itext('key4'), 'test value 4 en_us d project')
        
        
        
if __name__ == "__main__":
    unittest.main()
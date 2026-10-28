import unittest
import os
import filecmp

class TestSpecialForcesStartup(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.ws_root = r'c:\Program Files (x86)\Steam\steamapps\workshop\content\394360\3513811852'
        self.rel_path = os.path.join('common', 'on_actions', 'tfr_special_forces_on_actions.txt')
        self.repo_file = os.path.join(self.repo_root, self.rel_path)
        self.ws_file = os.path.join(self.ws_root, self.rel_path)

    def test_files_exist_and_match(self):
        self.assertTrue(os.path.exists(self.repo_file), 'Repo file must exist')
        self.assertTrue(os.path.exists(self.ws_file), 'Workshop file must exist')
        self.assertTrue(filecmp.cmp(self.repo_file, self.ws_file, shallow=False), 'Repo and Workshop files must be identical')

    def test_special_forces_unlocked_on_startup(self):
        with open(self.repo_file, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn('on_startup', content)
        self.assertIn('every_country', content)
        self.assertIn('set_technology', content)
        self.assertIn('tech_mountaineers = 1', content)
        self.assertIn('marines = 1', content)
        self.assertIn('paratroopers = 1', content)
        self.assertIn('rangers_tech = 1', content)

if __name__ == '__main__':
    unittest.main()

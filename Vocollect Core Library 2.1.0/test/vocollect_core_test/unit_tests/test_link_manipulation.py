
import mock_catalyst #@UnusedImport
from vocollect_core_test.base_test_case import BaseTestCaseCore
import unittest
from vocollect_core.dialog.ready_prompt import ReadyPromptExecutor
import voice

CONFIRM_YES_LINK = "Link10"
CONFIRM_NO_LINK = "Link11"
READY_PROMPT_DEFAULT_LINK = "Link13"
WAS_HTTP_POSTED_LINK = "Link18"
DIALOG_TIME_OUT_LINK = "Link19"


class TestLinkManipulation(BaseTestCaseCore):
    def test_move_link(self):
        # validate links are moved or KeyError thrown
        dialog = self._get_dialog_objects()[1]
        dialog._move_link(DIALOG_TIME_OUT_LINK, "StartHere", "ReadyPrompt")
        self.assertIn(dialog.links[DIALOG_TIME_OUT_LINK], dialog.nodes["StartHere"].out_links)
        self.assertIn(dialog.links[DIALOG_TIME_OUT_LINK], dialog.nodes["ReadyPrompt"].in_links)
        self.assertNotIn(dialog.links[DIALOG_TIME_OUT_LINK], dialog.nodes["ReadyComplete"].in_links)
        self.assertRaises(KeyError, dialog._move_link, DIALOG_TIME_OUT_LINK, "StartHere", "NonNode")
        self.assertRaises(KeyError, dialog._move_link, "NonLink", "StartHere", "ConfirmPrompt")

        # validate functionality of moved links
        executor, dialog = self._get_dialog_objects()
        dialog._move_link("main", "StartHere", "ReadyPrompt")
        dialog.links["NewLink"] = voice.Link("NewLink",
                                             dialog.nodes["StartHere"],
                                             dialog.nodes["CheckConfirm"],
                                             existing_vocab = ["stop"])
        mock_catalyst.post_dialog_responses("ready", "stop")
        result = executor.get_results()
        self.validate_prompts("Test prompt", "Test prompt")
        self.assertEquals(result, "stop")

        executor, dialog = self._get_dialog_objects()
        dialog.set_additional_vocab({"stop": True})
        dialog._move_link(CONFIRM_YES_LINK, "ConfirmPrompt", "ReadyPrompt")
        dialog._move_link(CONFIRM_NO_LINK, "ConfirmPrompt", "ReadyComplete")
        mock_catalyst.post_dialog_responses("stop", "yes", "stop", "no")
        result = executor.get_results()
        self.validate_prompts("Test prompt", "stop, correct?", "Test prompt", "stop, correct?")
        self.assertEquals("stop", result)

    def test_remove_link(self):
        dialog = self._get_dialog_objects()[1]
        dialog._remove_link(DIALOG_TIME_OUT_LINK)
        # Validate dialog.links is list of str, not Link objects,
        # then ensure DIALOG_TIME_OUT_LINK has been removed
        self.assertIn(WAS_HTTP_POSTED_LINK, dialog.links)
        self.assertNotIn(DIALOG_TIME_OUT_LINK, dialog.links)
        self.assertEquals(2, len(dialog.nodes["ReadyComplete"].in_links))
        self.assertRaises(KeyError, dialog._remove_link, "NonLink")

    def test_multi_move(self):
        # tests moving a link multiple times before executing dialog
        executor, dialog = self._get_dialog_objects()
        # move to same node
        for i in range(0, 3): #@UnusedVariable
            dialog._move_link("main", "StartHere", "CheckConfirm")
        # move to different node
        for i in range(0, 3): #@UnusedVariable
            dialog._move_link("main", "StartHere", "ReadyComplete")
        for i in range(0, 3): #@UnusedVariable
            dialog._move_link("main", "StartHere", "CheckConfirm")
            dialog._move_link("main", "StartHere", "ConfirmPrompt")
            dialog._move_link("main", "StartHere", "StartHere")
            dialog._move_link("main", "StartHere", "ReadyComplete")
        mock_catalyst.post_dialog_responses("ready")
        executor.get_results()
        self.validate_prompts("Test prompt")

    def test_end_dialog(self):
        executor, dialog = self._get_dialog_objects()
        dialog._remove_link(READY_PROMPT_DEFAULT_LINK)
        dialog.set_additional_vocab({"0": True})
        mock_catalyst.post_dialog_responses("0", "yes")
        result = executor.get_results()
        # validate responses not consumed, then clear for validate_prompts
        self.assertEquals(2, len(mock_catalyst.response_queue))
        mock_catalyst.response_queue = []
        self.validate_prompts("Test prompt")
        self.assertEquals(None, result)

    def _get_dialog_objects(self):
        ''' convenience function to return a simple Ready executor and dialog tuple '''
        executor = ReadyPromptExecutor("Test prompt", True, "Test help message")
        dialog = executor.dialog
        self.assertEqual(executor._dialog, dialog)
        return executor, dialog

if __name__ == "__main__":
    unittest.main()
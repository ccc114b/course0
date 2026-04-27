import unittest
import os
import sys
import subprocess
import shutil

sys.path.insert(0, os.path.dirname(__file__))

import fulltext0

CORPUS = "_data/corpus.txt"
IDX_PATH = "_index/data.idx"
OFF_PATH = "_index/offsets.bin"
TEST_DIR = os.path.dirname(os.path.abspath(__file__)) or "."

class TestTokenize(unittest.TestCase):
    def test_ascii(self):
        tokens = fulltext0.tokenize("hello world")
        self.assertIn("hello", tokens)
        self.assertIn("world", tokens)

    def test_chinese(self):
        tokens = fulltext0.tokenize("系統設計")
        self.assertIn("系統", tokens)
        self.assertIn("系", tokens)
        self.assertIn("統", tokens)

    def test_mixed(self):
        tokens = fulltext0.tokenize("hello 系統 world")
        self.assertIn("hello", tokens)
        self.assertIn("系統", tokens)
        self.assertIn("world", tokens)

    def test_empty(self):
        tokens = fulltext0.tokenize("")
        self.assertEqual(tokens, [])

class TestIndexBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(IDX_PATH):
            os.remove(IDX_PATH)
        if os.path.exists(OFF_PATH):
            os.remove(OFF_PATH)
        result = fulltext0.build(CORPUS, IDX_PATH, OFF_PATH)
        assert result == 0, "Index build failed"

    def test_build_creates_index(self):
        self.assertTrue(os.path.exists(IDX_PATH))

class TestIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(IDX_PATH):
            fulltext0.build(CORPUS, IDX_PATH, OFF_PATH)
        cls.idx = fulltext0.Index(IDX_PATH, OFF_PATH)

    @classmethod
    def tearDownClass(cls):
        cls.idx.close()

    def test_index_stats(self):
        stats = self.idx.stats()
        self.assertEqual(stats.num_docs, 1000)
        self.assertGreater(stats.num_terms, 0)

    def test_english_single_word(self):
        doc_ids = self.idx.query("system")
        self.assertGreater(len(doc_ids), 10)

    def test_chinese_single_word(self):
        doc_ids = self.idx.query("系統")
        self.assertGreater(len(doc_ids), 5)

    def test_chinese_bigram(self):
        doc_ids = self.idx.query("處理")
        self.assertGreater(len(doc_ids), 5)

    def test_no_result(self):
        doc_ids = self.idx.query("xyznonexistent999")
        self.assertEqual(len(doc_ids), 0)

    def test_get_lines(self):
        doc_ids = self.idx.query("處理器")
        self.assertGreater(len(doc_ids), 0)
        lines = self.idx.get_lines(CORPUS, doc_ids[:3])
        self.assertEqual(len(lines), 3)
        for line in lines:
            self.assertIn("處理器", line)

class TestIntegration(unittest.TestCase):
    def test_version(self):
        self.assertIsNotNone(fulltext0.__version__)
        self.assertEqual(fulltext0.__version__, "0.1.0")

    def test_context_manager(self):
        with fulltext0.Index(IDX_PATH, OFF_PATH) as idx:
            stats = idx.stats()
            self.assertGreater(stats.num_docs, 0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
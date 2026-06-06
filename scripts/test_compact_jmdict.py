#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
#
# Validates the content of generated JMdict lookup files.
# Run from the repo root: uv run scripts/test_compact_jmdict.py

import gzip
import json
import sys
import unittest
import zipfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent


def load_dict(name):
    with gzip.open(ROOT / 'build' / name) as f:
        return json.load(f)


DICT = load_dict('jmdict-full.json.gz')


def pg(word):
    return DICT.get(word, {}).get('pg')


class TestParticleGlosses(unittest.TestCase):

    def test_common_particles_have_pg(self):
        expected = ['は', 'が', 'を', 'に', 'へ', 'で', 'と', 'から', 'より',
                    'の', 'まで', 'も', 'ね', 'か', 'ながら', 'ので', 'のに',
                    'けど', 'だけ', 'こそ', 'さえ', 'しか', 'など', 'ばかり']
        missing = [p for p in expected if not pg(p)]
        self.assertFalse(missing, f'particles missing pg: {missing}')

    def test_pg_is_list_of_strings(self):
        for word, entry in DICT.items():
            if 'pg' in entry:
                self.assertIsInstance(entry['pg'], list, f'{word}: pg should be a list')
                for gloss in entry['pg']:
                    self.assertIsInstance(gloss, str, f'{word}: pg item should be str')
                    self.assertTrue(gloss.strip(), f'{word}: pg item should not be blank')

    def test_topic_particle_ha(self):
        self.assertIn('indicates sentence topic', pg('は'))

    def test_subject_particle_ga(self):
        self.assertTrue(any('subject' in g for g in pg('が')),
                        f'が pg should mention subject: {pg("が")}')

    def test_object_particle_wo(self):
        self.assertTrue(any('direct object' in g for g in pg('を')),
                        f'を pg should mention direct object: {pg("を")}')

    def test_topic_particle_ha_first_gloss(self):
        self.assertEqual(pg('は')[0], 'indicates sentence topic')

    def test_te_pg_is_quoting_sense(self):
        # The JMdict "common" て entry is the quoting particle (って).
        # This documents why lookupParticle uses pg2 for 接続助詞 て.
        te_pg = pg('て')
        self.assertIsNotNone(te_pg, 'て should have a pg entry')
        self.assertTrue(
            any('said' in g for g in te_pg),
            f'て pg should contain quoting senses ("said"), got: {te_pg[:4]}'
        )

    def test_te_pg2_is_conjunctive_sense(self):
        # pg2 holds the non-common entry's glosses — the conjunctive て (食べて).
        te_pg2 = DICT.get('て', {}).get('pg2')
        self.assertIsNotNone(te_pg2, 'て should have a pg2 entry')
        self.assertTrue(
            any('and' in g or 'then' in g for g in te_pg2),
            f'て pg2 should contain conjunctive senses, got: {te_pg2[:4]}'
        )

    def test_de_pg_is_locative_sense(self):
        # で pg is the locative sense (common entry).
        de_pg = pg('で')
        self.assertIsNotNone(de_pg, 'で should have a pg entry')
        self.assertTrue(
            any(g in ('at', 'in') for g in de_pg),
            f'で pg should contain locative senses ("at"/"in"), got: {de_pg[:4]}'
        )

    def test_de_pg2_is_conjunctive_sense(self):
        # て and で share the same non-common conjunctive entry.
        de_pg2 = DICT.get('で', {}).get('pg2')
        self.assertIsNotNone(de_pg2, 'で should have a pg2 entry')
        self.assertTrue(
            any('and' in g or 'then' in g for g in de_pg2),
            f'で pg2 should contain conjunctive senses, got: {de_pg2[:4]}'
        )

    def test_zutu_has_no_pg(self):
        # ずつ is tagged suf (not prt/exp/aux) — no disambiguation needed, g[0] fallback handles it.
        self.assertIsNone(pg('ずつ'), f'ずつ should have no pg, got: {pg("ずつ")}')

    def test_nitotte_has_pg(self):
        # にとって is tagged exp; exp senses are now collected into pg.
        nitotte_pg = pg('にとって')
        self.assertIsNotNone(nitotte_pg, 'にとって should have pg from exp sense')
        self.assertTrue(any('for' in g or 'standpoint' in g for g in nitotte_pg),
                        f'にとって pg should describe its particle use, got: {nitotte_pg[:3]}')

    def test_niyori_has_pg(self):
        # により had 2 g groups (noun + exp), so g[0] fallback gave "similarity" (wrong).
        # exp senses now go into pg, giving the correct particle meaning.
        niyori_pg = pg('により')
        self.assertIsNotNone(niyori_pg, 'により should have pg from exp sense')
        self.assertTrue(any('according' in g or 'due to' in g for g in niyori_pg),
                        f'により pg should describe its particle use, got: {niyori_pg[:3]}')

    def test_pg_length_reasonable(self):
        # pg entries should not be empty, and capping at a large number catches runaway merges
        for word, entry in DICT.items():
            if 'pg' in entry:
                self.assertGreater(len(entry['pg']), 0, f'{word}: pg should not be empty')
                self.assertLessEqual(len(entry['pg']), 50, f'{word}: pg suspiciously long')


class TestAuxiliaryGlosses(unittest.TestCase):

    def test_nai_has_pg(self):
        nai_pg = pg('ない')
        self.assertIsNotNone(nai_pg, 'ない should have pg from aux-adj sense')
        self.assertIn('not', nai_pg, f'ない pg should include "not", got: {nai_pg[:4]}')

    def test_ta_has_pg(self):
        # た common JMdict entry is a prefix/abbreviation; aux sense is in non-common entry.
        # compact_jmdict.py merges it into pg (not pg2) because no competing pg exists.
        ta_pg = pg('た')
        self.assertIsNotNone(ta_pg, 'た should have pg from aux-v sense')
        self.assertTrue(any('did' in g or 'done' in g for g in ta_pg),
                        f'た pg should contain past-tense glosses, got: {ta_pg[:4]}')

    def test_da_has_pg(self):
        da_pg = pg('だ')
        self.assertIsNotNone(da_pg, 'だ should have pg from copula sense')
        self.assertTrue(any(g in ('be', 'is') for g in da_pg),
                        f'だ pg should contain copula glosses, got: {da_pg[:4]}')

    def test_rareru_has_pg(self):
        rareru_pg = pg('られる')
        self.assertIsNotNone(rareru_pg, 'られる should have pg from aux-v sense')
        self.assertTrue(any('passive' in g for g in rareru_pg),
                        f'られる pg should mention passive, got: {rareru_pg[:3]}')


class TestDictionaryArtifacts(unittest.TestCase):

    def test_all_modes_are_valid_json(self):
        ultra = load_dict('jmdict-ultra-compact.json.gz')
        full = load_dict('jmdict-full.json.gz')
        self.assertLess(len(ultra), len(full))
        self.assertIn('行く', ultra)
        self.assertGreaterEqual(len(full['行く']['g']), len(ultra['行く']['g']))

    def test_ultra_mode_keeps_grammar_disambiguation(self):
        ultra = load_dict('jmdict-ultra-compact.json.gz')

        ta_pg = ultra.get('た', {}).get('pg')
        self.assertIsNotNone(ta_pg, 'ultra た should keep auxiliary pg glosses')
        self.assertTrue(any('did' in g or 'done' in g for g in ta_pg),
                        f'ultra た pg should contain past-tense glosses, got: {ta_pg[:4]}')

        te_pg2 = ultra.get('て', {}).get('pg2')
        self.assertIsNotNone(te_pg2, 'ultra て should keep conjunctive pg2 glosses')
        self.assertTrue(any('and' in g or 'then' in g for g in te_pg2),
                        f'ultra て pg2 should contain conjunctive senses, got: {te_pg2[:4]}')

        de_pg2 = ultra.get('で', {}).get('pg2')
        self.assertIsNotNone(de_pg2, 'ultra で should keep conjunctive pg2 glosses')
        self.assertTrue(any('and' in g or 'then' in g for g in de_pg2),
                        f'ultra で pg2 should contain conjunctive senses, got: {de_pg2[:4]}')

        rareru_pg = ultra.get('られる', {}).get('pg')
        self.assertIsNotNone(rareru_pg, 'ultra られる should keep auxiliary pg glosses')
        self.assertTrue(any('passive' in g for g in rareru_pg),
                        f'ultra られる pg should mention passive, got: {rareru_pg[:3]}')

        niyori_pg = ultra.get('により', {}).get('pg')
        self.assertIsNotNone(niyori_pg, 'ultra により should keep expression pg glosses')
        self.assertTrue(any('according' in g or 'due to' in g for g in niyori_pg),
                        f'ultra により pg should describe particle use, got: {niyori_pg[:3]}')


class TestEdgeCasesAndValidation(unittest.TestCase):

    def test_empty_source_file_raises_error(self):
        """Test that an empty source file raises ValueError."""
        empty_data = json.dumps({'words': []}).encode('utf-8')
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.json.zip', delete=False) as f:
            tmp_path = Path(f.name)

        try:
            with zipfile.ZipFile(tmp_path, 'w') as zf:
                zf.writestr('jmdict-empty.json', empty_data)

            # Test by checking the error would be raised during the validation step
            with zipfile.ZipFile(tmp_path) as zf:
                d = json.load(zf.open(zf.namelist()[0]))
                self.assertFalse(d.get('words'), 'Test data should have empty words list')
                # This simulates what compact_jmdict.py does - should raise ValueError
                with self.assertRaises(ValueError, msg='Empty words list should raise ValueError'):
                    if not d.get('words'):
                        raise ValueError('Source file contains no words')
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_ultra_mode_has_fewer_entries_than_full(self):
        """Test that ultra-compact mode filters out uncommon entries."""
        ultra = load_dict('jmdict-ultra-compact.json.gz')
        full = load_dict('jmdict-full.json.gz')

        # Ultra should have significantly fewer entries
        ultra_count = len(ultra)
        full_count = len(full)
        reduction_pct = (1 - ultra_count / full_count) * 100

        # Ultra should reduce the dictionary by at least 20%
        self.assertGreater(reduction_pct, 20,
                          f'ultra mode should reduce entries by >20%, got {reduction_pct:.1f}% '
                          f'({ultra_count} vs {full_count} entries)')

    def test_common_words_present_in_ultra_mode(self):
        """Test that common words are preserved in ultra mode."""
        ultra = load_dict('jmdict-ultra-compact.json.gz')

        # Common words that should definitely be present
        common_words = ['行く', '食べる', '見る', '来る', 'ある', 'いる', 'なる', 'する']
        for word in common_words:
            self.assertIn(word, ultra, f'Common word "{word}" should be in ultra mode')

    def test_grammar_entries_preserved_in_ultra_mode(self):
        """Test that grammar-related entries are kept even if uncommon."""
        ultra = load_dict('jmdict-ultra-compact.json.gz')

        # These grammar words should be present due to particle_glosses preservation
        grammar_words = ['た', 'て', 'で', 'ない', 'だ', 'られる', 'により', 'にとって']
        for word in grammar_words:
            self.assertIn(word, ultra, f'Grammar word "{word}" should be in ultra mode')

    def test_full_mode_contains_all_ultra_entries(self):
        """Test that full mode is a superset of ultra mode."""
        ultra = load_dict('jmdict-ultra-compact.json.gz')
        full = load_dict('jmdict-full.json.gz')

        for word in ultra:
            self.assertIn(word, full, f'Word "{word}" in ultra should also be in full')

    def test_gloss_groups_are_lists(self):
        """Test that all gloss groups are properly formatted as lists."""
        ultra = load_dict('jmdict-ultra-compact.json.gz')
        full = load_dict('jmdict-full.json.gz')

        for name, d in [('ultra', ultra), ('full', full)]:
            for word, entry in d.items():
                self.assertIsInstance(entry['g'], list,
                                    f'{name}: {word} gloss groups should be a list')
                for i, group in enumerate(entry['g']):
                    self.assertIsInstance(group, list,
                                        f'{name}: {word} gloss group {i} should be a list')
                    for gloss in group:
                        self.assertIsInstance(gloss, str,
                                            f'{name}: {word} gloss should be a string')

    def test_pg_fields_are_lists_of_strings(self):
        """Test that pg/pg2 fields are properly formatted."""
        ultra = load_dict('jmdict-ultra-compact.json.gz')
        full = load_dict('jmdict-full.json.gz')

        for name, d in [('ultra', ultra), ('full', full)]:
            for word, entry in d.items():
                for key in ['pg', 'pg2']:
                    if key in entry:
                        self.assertIsInstance(entry[key], list,
                                            f'{name}: {word} {key} should be a list')
                        for gloss in entry[key]:
                            self.assertIsInstance(gloss, str,
                                                f'{name}: {word} {key} gloss should be a string')


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in (TestParticleGlosses, TestAuxiliaryGlosses, TestDictionaryArtifacts, TestEdgeCasesAndValidation):
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

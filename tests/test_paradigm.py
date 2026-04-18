"""
Unit tests for scripts/paradigm.py
Run with: python -m pytest tests/test_paradigm.py -v
"""

import pytest
from scripts.paradigm import CellID, ParadigmMapper, type_to_conjugation


class TestCellID:
    def test_verb_cell_id_to_string(self):
        cell = CellID(
            stem="qal",
            conjugation="qatal",
            person="third",
            gender="masculine",
            number="singular",
            is_noun=False,
        )
        assert "qal" in cell.to_string()
        assert "qatal" in cell.to_string()
        assert "third" in cell.to_string()

    def test_noun_cell_id_to_string(self):
        cell = CellID(
            stem="",
            conjugation="common",
            person=None,
            gender="masculine",
            number="sg",
            state="abs",
            is_noun=True,
        )
        assert cell.to_string() == "common.sg.abs"

    def test_infinitive_cell_no_person(self):
        cell = CellID(
            stem="qal",
            conjugation="infinitive_construct",
            person=None,
            gender=None,
            number=None,
            is_noun=False,
        )
        assert cell.to_string() == "qal.infinitive_construct"

    def test_participle_cell(self):
        cell = CellID(
            stem="piel",
            conjugation="participle_active",
            person="",
            gender="feminine",
            number="singular",
            is_noun=False,
        )
        assert "piel" in cell.to_string()
        assert "participle_active" in cell.to_string()


class TestParadigmMapper:
    def setup_method(self):
        self.mapper = ParadigmMapper()

    def test_type_to_conjugation_maps_qatal(self):
        assert type_to_conjugation["qatal"] == "qatal"

    def test_type_to_conjugation_maps_yiqtol(self):
        assert type_to_conjugation["yiqtol"] == "yiqtol"

    def test_type_to_conjugation_maps_imperative(self):
        assert type_to_conjugation["imperative"] == "imperative"

    def test_type_to_conjugation_maps_infinitive_construct(self):
        assert type_to_conjugation["infinitive construct"] == "infinitive_construct"

    def test_type_to_conjugation_maps_participle_active(self):
        assert type_to_conjugation["participle active"] == "participle_active"

    def test_map_verb_qatal(self):
        form = {
            "type": "qatal",
            "person": "third",
            "gender": "masculine",
            "number": "singular",
        }
        cell = self.mapper.map_form(form, "בָּרָא", "qal")
        assert cell is not None
        assert cell.stem == "qal"
        assert cell.conjugation == "qatal"
        assert cell.person == "third"
        assert cell.gender == "masculine"
        assert cell.number == "singular"

    def test_map_verb_wayyiqtol(self):
        form = {
            "type": "wayyiqtol",
            "person": "third",
            "gender": "masculine",
            "number": "singular",
        }
        cell = self.mapper.map_form(form, "אָמַר", "qal")
        assert cell is not None
        assert cell.conjugation == "wayyiqtol"

    def test_map_verb_yiqtol(self):
        form = {
            "type": "yiqtol",
            "person": "first",
            "gender": "common",
            "number": "singular",
        }
        cell = self.mapper.map_form(form, "רָאָה", "qal")
        assert cell is not None
        assert cell.conjugation == "yiqtol"
        assert cell.person == "first"

    def test_map_verb_imperative(self):
        form = {
            "type": "imperative",
            "person": "second",
            "gender": "masculine",
            "number": "singular",
        }
        cell = self.mapper.map_form(form, "קוּם", "qal")
        assert cell is not None
        assert cell.conjugation == "imperative"
        assert cell.person == "second"

    def test_map_verb_infinitive_construct(self):
        form = {
            "type": "infinitive construct",
            "person": "",
            "gender": "",
            "number": "",
        }
        cell = self.mapper.map_form(form, "לָכַת", "qal")
        assert cell is not None
        assert cell.conjugation == "infinitive_construct"

    def test_map_verb_weqatal(self):
        form = {
            "type": "weqatal",
            "person": "second",
            "gender": "masculine",
            "number": "singular",
        }
        cell = self.mapper.map_form(form, "בָּרָא", "piel")
        assert cell is not None
        assert cell.conjugation == "weqatal"

    def test_map_verb_jussive(self):
        form = {
            "type": "jussive",
            "person": "third",
            "gender": "masculine",
            "number": "singular",
        }
        cell = self.mapper.map_form(form, "הָיָה", "qal")
        assert cell is not None
        assert cell.conjugation == "jussive"

    def test_map_verb_cohortative(self):
        form = {
            "type": "cohortative",
            "person": "first",
            "gender": "common",
            "number": "singular",
        }
        cell = self.mapper.map_form(form, "רָאָה", "qal")
        assert cell is not None
        assert cell.conjugation == "cohortative"

    def test_map_verb_niphal(self):
        form = {
            "type": "qatal",
            "person": "third",
            "gender": "masculine",
            "number": "singular",
        }
        cell = self.mapper.map_form(form, "נִבְרָא", "niphal")
        assert cell is not None
        assert cell.stem == "niphal"

    def test_map_verb_piel(self):
        form = {
            "type": "qatal",
            "person": "third",
            "gender": "masculine",
            "number": "singular",
        }
        cell = self.mapper.map_form(form, "דִבֵּר", "piel")
        assert cell is not None
        assert cell.stem == "piel"

    def test_map_verb_hiphil(self):
        form = {
            "type": "qatal",
            "person": "third",
            "gender": "masculine",
            "number": "singular",
        }
        cell = self.mapper.map_form(form, "הֲלִיךְ", "hiphil")
        assert cell is not None
        assert cell.stem == "hiphil"

    def test_map_verb_hophal(self):
        form = {
            "type": "qatal",
            "person": "third",
            "gender": "masculine",
            "number": "singular",
        }
        cell = self.mapper.map_form(form, "הוּבַל", "hophal")
        assert cell is not None
        assert cell.stem == "hophal"

    def test_map_verb_hithpael(self):
        form = {
            "type": "qatal",
            "person": "third",
            "gender": "masculine",
            "number": "singular",
        }
        cell = self.mapper.map_form(form, "הִתְקַדֵּשׁ", "hithpael")
        assert cell is not None
        assert cell.stem == "hithpael"

    def test_map_noun_common(self):
        form = {
            "type": "common",
            "gender": "masculine",
            "number": "singular",
            "state": "absolute",
        }
        cell = self.mapper.map_form(form, "סֵפֶר", "")
        assert cell is not None
        assert cell.is_noun is True
        assert cell.conjugation == "common"

    def test_map_noun_proper(self):
        form = {
            "type": "proper",
            "gender": "",
            "number": "singular",
            "state": "absolute",
        }
        cell = self.mapper.map_form(form, "יְהוּדָה", "")
        assert cell is not None
        assert cell.conjugation == "proper"

    def test_map_noun_plural(self):
        form = {
            "type": "common",
            "gender": "masculine",
            "number": "plural",
            "state": "absolute",
        }
        cell = self.mapper.map_form(form, "סְפָרִים", "")
        assert cell is not None
        assert cell.number == "p"

    def test_map_noun_construct(self):
        form = {
            "type": "common",
            "gender": "masculine",
            "number": "singular",
            "state": "construct",
        }
        cell = self.mapper.map_form(form, "סֵפֶר", "")
        assert cell is not None
        assert cell.state == "c"

    def test_map_noun_default_gender(self):
        form = {
            "type": "common",
            "gender": "both",
            "number": "singular",
            "state": "absolute",
        }
        cell = self.mapper.map_form(form, "אָדָם", "")
        assert cell is not None
        assert cell.gender == "masculine"

    def test_map_verb_participle_passive(self):
        form = {
            "type": "participle passive",
            "person": "",
            "gender": "masculine",
            "number": "singular",
            "state": "absolute",
        }
        cell = self.mapper.map_form(form, "נִכְתָּב", "niphal")
        assert cell is not None
        assert cell.conjugation == "participle_passive"

    def test_clean_stem_unknown(self):
        cleaned = self.mapper._clean_stem("unknown: z")
        assert cleaned == "qal"

    def test_clean_stem_empty_defaults_to_qal(self):
        cleaned = self.mapper._clean_stem("")
        assert cleaned == "qal"

    def test_validate_attestation_returns_stats(self):
        results = self.mapper.validate_attestation()
        assert "total_forms" in results
        assert "mapped" in results
        assert "unmapped" in results
        assert results["total_forms"] > 0


class TestMasterParadigmYaml:
    def test_paradigm_yaml_loads(self):
        import yaml
        from pathlib import Path

        path = Path(__file__).parent.parent / "lexicon" / "master_paradigm.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "stems" in data
        assert "verb_conjugations" in data

    def test_all_seven_binyanim_present(self):
        import yaml
        from pathlib import Path

        path = Path(__file__).parent.parent / "lexicon" / "master_paradigm.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        expected = {"qal", "niphal", "piel", "pual", "hiphil", "hophal", "hithpael"}
        assert set(data["stems"]) == expected

    def test_verb_conjugations_complete(self):
        import yaml
        from pathlib import Path

        path = Path(__file__).parent.parent / "lexicon" / "master_paradigm.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        conjugations = set(data["verb_conjugations"])
        assert "qatal" in conjugations
        assert "yiqtol" in conjugations
        assert "imperative" in conjugations
        assert "infinitive_construct" in conjugations
        assert "infinitive_absolute" in conjugations
        assert "participle_active" in conjugations
        assert "participle_passive" in conjugations
        assert "jussive" in conjugations
        assert "cohortative" in conjugations
        assert "wayyiqtol" in conjugations
        assert "weqatal" in conjugations


class TestPronominalSuffixes:
    def test_verb_suffixes_defined(self):
        import yaml
        from pathlib import Path

        path = Path(__file__).parent.parent / "lexicon" / "master_paradigm.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "verb_suffixes" in data
        assert "1cs" in data["verb_suffixes"]
        assert "3mp" in data["verb_suffixes"]

    def test_possessive_suffixes_defined(self):
        import yaml
        from pathlib import Path

        path = Path(__file__).parent.parent / "lexicon" / "master_paradigm.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "possessive_suffixes" in data
        assert "1cs" in data["possessive_suffixes"]
        assert "3ms" in data["possessive_suffixes"]


class TestProclitics:
    def test_definite_article_defined(self):
        import yaml
        from pathlib import Path

        path = Path(__file__).parent.parent / "lexicon" / "master_paradigm.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "definite_article" in data

    def test_conjunction_defined(self):
        import yaml
        from pathlib import Path

        path = Path(__file__).parent.parent / "lexicon" / "master_paradigm.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "conjunction" in data

    def test_prepositions_defined(self):
        import yaml
        from pathlib import Path

        path = Path(__file__).parent.parent / "lexicon" / "master_paradigm.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "prepositions" in data
        assert "beth" in data["prepositions"]
        assert "kaph" in data["prepositions"]
        assert "lamed" in data["prepositions"]

    def test_morpheme_order_defined(self):
        import yaml
        from pathlib import Path

        path = Path(__file__).parent.parent / "lexicon" / "master_paradigm.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "morpheme_order" in data


class TestCellIDWithSuffix:
    def test_cell_id_with_suffix_to_string(self):
        from scripts.paradigm import CellID

        cell = CellID(
            stem="qal",
            conjugation="qatal",
            person="third",
            gender="masculine",
            number="singular",
            is_noun=False,
            suffix="3ms",
        )
        assert "qal" in cell.to_string()
        assert "qatal" in cell.to_string()
        assert "3ms" in cell.to_string()

    def test_cell_id_with_suffix_to_string_verb(self):
        from scripts.paradigm import CellID

        cell = CellID(
            stem="piel",
            conjugation="qatal",
            person="first",
            gender="common",
            number="plural",
            is_noun=False,
            suffix="1cp",
        )
        assert "piel" in cell.to_string()
        assert "1cp" in cell.to_string()

    def test_cell_id_noun_with_possessive(self):
        from scripts.paradigm import CellID

        cell = CellID(
            stem="",
            conjugation="common",
            person=None,
            gender="masculine",
            number="s",
            state="a",
            is_noun=True,
            suffix="Sp1cs",
        )
        result = cell.to_string()
        assert "common" in result
        assert "Sp1cs" in result


class TestMorphemeMapping:
    def test_map_suffix_from_morph(self):
        from scripts.paradigm import ParadigmMapper

        mapper = ParadigmMapper()
        suffix = mapper._map_suffix("Sp1cs")
        assert suffix == "1cs"

    def test_map_suffix_from_morph_3mp(self):
        from scripts.paradigm import ParadigmMapper

        mapper = ParadigmMapper()
        suffix = mapper._map_suffix("Sp3mp")
        assert suffix == "3mp"

    def test_map_suffix_empty(self):
        from scripts.paradigm import ParadigmMapper

        mapper = ParadigmMapper()
        suffix = mapper._map_suffix("")
        assert suffix is None

    def test_verb_with_suffix_mapping(self):
        from scripts.paradigm import ParadigmMapper

        mapper = ParadigmMapper()
        form = {
            "type": "qatal",
            "person": "third",
            "gender": "masculine",
            "number": "singular",
            "pron_suffix": {"morph": "Sp3ms"},
            "pron_suffix_morph": "Sp3ms",
        }
        cell = mapper.map_form(form, "סֵפֶר", "qal")
        assert cell is not None
        assert cell.suffix == "3ms"

    def test_noun_with_possessive_suffix(self):
        from scripts.paradigm import ParadigmMapper

        mapper = ParadigmMapper()
        form = {
            "type": "common",
            "gender": "masculine",
            "number": "singular",
            "state": "absolute",
            "pron_suffix": {"morph": "Sp1cs"},
            "pron_suffix_morph": "Sp1cs",
        }
        cell = mapper.map_form(form, "סֵפֶר", "")
        assert cell is not None
        assert cell.suffix == "1cs"


class TestPrefixExtraction:
    def test_extract_definite_article(self):
        from scripts.paradigm import ParadigmMapper

        mapper = ParadigmMapper()
        form = {
            "type": "common",
            "prefixes": ["R"],
        }
        prefixes = mapper._extract_prefixes(form)
        assert len(prefixes) == 1
        assert prefixes[0].prefix_type == "definite_article"

    def test_extract_conjunction(self):
        from scripts.paradigm import ParadigmMapper

        mapper = ParadigmMapper()
        form = {
            "type": "qatal",
            "prefixes": ["C"],
        }
        prefixes = mapper._extract_prefixes(form)
        assert len(prefixes) == 1
        assert prefixes[0].prefix_type == "conjunction"

    def test_extract_multiple_prefixes(self):
        from scripts.paradigm import ParadigmMapper

        mapper = ParadigmMapper()
        form = {
            "type": "common",
            "prefixes": ["C", "R"],
        }
        prefixes = mapper._extract_prefixes(form)
        assert len(prefixes) == 2

    def test_extract_no_prefixes(self):
        from scripts.paradigm import ParadigmMapper

        mapper = ParadigmMapper()
        form = {"type": "common", "prefixes": []}
        prefixes = mapper._extract_prefixes(form)
        assert len(prefixes) == 0

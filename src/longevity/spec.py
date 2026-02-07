# =========================
# LONGEVITY 4.8 — DICT-ONLY v2.2 (MERGED, KOMPLET)
# =========================
from typing import Any

PIPELINE = [
    "base_by_block",
    "apply_schedule_rules",
    "apply_constraints",
    "apply_supplement_exclusions",
    "apply_block_exclusions",
    "apply_events",
    "apply_global_exceptions",
]

CONFIG = {
    "week_start": 0,  # 0=Mon
    "weekday_indexing": "0=Mon..6=Sun",
    "month_week_definition": "days_1_7,8_14,15_21,22_28,29_end",
    "default_times_per_week_policy": "fixed_days",
    "fixed_days_semantics": "applies_within_each_calendar_week_mon_sun",
    # v2.2: normalizacja kolekcji wejściowych
    "collection_input_types_allowed": {"list", "set"},
    "collection_normalization": "sorted_list",
    "priority_resolution": {
        "precedence": [
            "apply_global_exceptions",  # zawsze ostatnie
            # i ma prawo skasować wszystko
            "apply_events",  # eventy i ich override (allow_only/remove_all)
            "apply_block_exclusions",  # blokowe wykluczenia
            "apply_supplement_exclusions",  # A excludes B
            "apply_constraints",  # constraint allowed/exclude/seasonal/require
            "apply_schedule_rules",  # częstotliwości
            "base_by_block",  # blok bazowy
        ],
        "notes": "Precedence = kolejność 'ostatnie słowo' "
        "przy sprzecznościach. OFF WEEK może skasować CORE.",
    },
    "override_semantics": {
        "allow_only": "after allow_only, list dnia = intersection(list, "
        "allowed_set) + required_event_supplements_if_missing",
        "remove_all": "after remove_all, list dnia = empty",
    },
    "event_day_selection": {
        "pulse": {
            "default_policy": "fixed_day_of_month",
            "month_week_selection_mapping": {
                1: [1, 2],
                2: [8, 9],  # fisetyna
                3: [15, 16],
                4: [22, 23],
                5: [29, 30],
            },
            "fallback_if_day_invalid": "next_valid_day_in_month",
        }
    },
}

BLOCK_CALENDAR = {
    1: "NAD",
    2: "MITO",
    3: "ANTIAGE",
    4: "DETOX",
    5: "NAD",
    6: "MITO",
    7: "ANTIAGE",
    8: "DETOX",
    9: "NAD",
    10: "ANTIAGE",
    11: "MITO",
    12: "DETOX",
}

BLOCKS = {
    "NAD": {"id": "NAD", "name": "NAD", "description": None, "enabled": True},
    "MITO": {
        "id": "MITO",
        "name": "MITO",
        "description": None,
        "enabled": True,
    },
    "ANTIAGE": {
        "id": "ANTIAGE",
        "name": "ANTI-AGE",
        "description": None,
        "enabled": True,
    },
    "DETOX": {
        "id": "DETOX",
        "name": "DETOX",
        "description": None,
        "enabled": True,
    },
}

CORE_SET = {"omega3_nko", "mg_zn_b6", "collagen", "probiotic", "d3k2"}

CONFLICTS = {
    "block_exclusions": {
        "NAD": {"curcumin_piperine", "lycopene", "astaxanthin", "r_ala"},
        "DETOX": {"q10_pqq_spermidine"},
        "MITO": set(),
        "ANTIAGE": set(),
    },
    # A excludes B (jednostronnie)
    "supplement_exclusions": {
        "nmn": {"curcumin_piperine", "astaxanthin", "lycopene"},
    },
    # v2.2: faza zgodna z PIPELINE
    "supplement_exclusions_policy": {
        "direction": "one_way",
        "apply_phase": "apply_supplement_exclusions",
    },
    "event_overrides": {
        "pulse_fisetin": {
            "effect": "allow_only",
            "allowed_set": set(CORE_SET) | {"fisetin_pulse"},
        },
        "off_week": {"effect": "remove_all"},
    },
}

GLOBAL_EXCEPTIONS = [
    {
        "id": "off_week",
        "type": "off_week",
        "start_date": None,  # runtime
        "week_of_year": None,  # runtime alternativa
        "duration_days": 7,
        "effect": "remove_all",
        "priority": 10000,
        "hard_exclusion_of_events": {"pulse_fisetin"},
        "notes": "OFF WEEK usuwa wszystko, także CORE.",
    }
]

EVENTS = {
    "pulse_fisetin": {
        "id": "pulse_fisetin",
        "type": "pulse",
        "months": [3, 6, 9, 12],
        "length_days": 2,
        "month_week_selection": 2,  # days 8-14
        "time_of_day": "morning",
        "capsules_per_day": 12,  # v2.2: twardo w schemacie
        "override_id": "pulse_fisetin",
        "priority": 9000,
    }
}

# =========================
# SUPPLEMENTS
# =========================

SUPPLEMENTS: dict[str, Any] = {
    # CORE
    "omega3_nko": {
        "id": "omega3_nko",
        "name": "Omega-3 NKO",
        "default_dose": None,
        "tags": {"CORE"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "omega3_daily",
                "type": "daily",
                "active_blocks": None,
                "params": {},
            }
        ],
        "priority": 100,
        "notes": None,
    },
    "mg_zn_b6": {
        "id": "mg_zn_b6",
        "name": "Mg + Zn + B6",
        "default_dose": None,
        "tags": {"CORE"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "mgzn_daily",
                "type": "daily",
                "active_blocks": None,
                "params": {},
            }
        ],
        "priority": 100,
        "notes": None,
    },
    "collagen": {
        "id": "collagen",
        "name": "Kolagen",
        "default_dose": None,
        "tags": {"CORE"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "collagen_daily",
                "type": "daily",
                "active_blocks": None,
                "params": {},
            }
        ],
        "priority": 100,
        "notes": None,
    },
    "probiotic": {
        "id": "probiotic",
        "name": "Probiotyki",
        "default_dose": None,
        "tags": {"CORE"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "probiotic_daily",
                "type": "daily",
                "active_blocks": None,
                "params": {},
            }
        ],
        "priority": 100,
        "notes": None,
    },
    "d3k2": {
        "id": "d3k2",
        "name": "D3K2",
        "default_dose": None,
        "tags": {"CORE"},
        "constraints": [
            {
                "id": "d3k2_seasonal",
                "type": "seasonal",
                "params": {"months_included": {10, 11, 12, 1, 2, 3}},
            }
        ],
        "schedule_rules": [
            {
                "id": "d3k2_daily",
                "type": "daily",
                "active_blocks": None,
                "params": {},
            }
        ],
        "priority": 60,
        "notes": "Zima; opcjonalnie latem (runtime flag).",
    },
    # NAD
    "nmn": {
        "id": "nmn",
        "name": "NMN",
        "default_dose": {
            "amount": None,
            "unit": None,
            "timing_hint": "morning",
        },
        "tags": {"NAD"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "nmn_4x_week",
                "type": "times_per_week",
                "active_blocks": {"NAD"},
                "params": {
                    "n": 4,
                    "selection_policy": "fixed_days",
                    "fixed_days": [0, 1, 3, 4],
                },
            }
        ],
        "priority": 80,
        "notes": None,
    },
    "pterostilbene_resveratrol": {
        "id": "pterostilbene_resveratrol",
        "name": "Pterostylben / Resweratrol",
        "default_dose": {
            "amount": None,
            "unit": None,
            "timing_hint": "morning",
        },
        "tags": {"NAD"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "ptr_same_as_nmn",
                "type": "week_pattern",
                "active_blocks": {"NAD"},
                "params": {"days_included": {0, 1, 3, 4}},
            }
        ],
        "priority": 70,
        "notes": "Dni jak NMN.",
    },
    "astragalus": {
        "id": "astragalus",
        "name": "Astragalus",
        "default_dose": None,
        "tags": {"NAD"},
        "constraints": [
            {
                "id": "astragalus_allowed_blocks",
                "type": "allowed_blocks",
                "params": {"blocks": {"NAD"}},
            }
        ],
        "schedule_rules": [
            {
                "id": "astragalus_cycle_12_4",
                "type": "cycle_weeks",
                "active_blocks": None,
                "params": {
                    "on_weeks": 12,
                    "off_weeks": 4,
                    "alignment": "custom_date",
                },
            }
        ],
        "priority": 55,
        "notes": None,
    },
    "phosphatidylserine": {
        "id": "phosphatidylserine",
        "name": "Fosfatydyloseryna",
        "default_dose": {
            "amount": None,
            "unit": None,
            "timing_hint": "evening",
        },
        "tags": {"NAD"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "ps_5on2off",
                "type": "week_pattern",
                "active_blocks": {"NAD"},
                "params": {"days_included": {0, 1, 2, 3, 4}},
            }
        ],
        "priority": 50,
        "notes": None,
    },
    "lions_mane": {
        "id": "lions_mane",
        "name": "Lion’s Mane",
        "default_dose": {
            "amount": None,
            "unit": None,
            "timing_hint": "morning",
        },
        "tags": {"NAD", "MITO"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "lm_5on2off",
                "type": "week_pattern",
                "active_blocks": {"NAD", "MITO"},
                "params": {"days_included": {0, 1, 2, 3, 4}},
            }
        ],
        "priority": 45,
        "notes": None,
    },
    # Ca-AKG (scalone)
    "ca_akg": {
        "id": "ca_akg",
        "name": "Ca-AKG",
        "default_dose": {
            "amount": None,
            "unit": None,
            "timing_hint": "morning",
        },
        "tags": {"NAD", "MITO"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "caakg_nad_2x",
                "type": "times_per_week",
                "active_blocks": {"NAD"},
                "params": {
                    "n": 2,
                    "selection_policy": "fixed_days",
                    "fixed_days": [1, 4],
                },
            },
            {
                "id": "caakg_mito_4x",
                "type": "times_per_week",
                "active_blocks": {"MITO"},
                "params": {
                    "n": 4,
                    "selection_policy": "fixed_days",
                    "fixed_days": [0, 1, 3, 5],
                },
            },
        ],
        "priority": 45,
        "notes": None,
    },
    # MITO
    "q10_pqq_spermidine": {
        "id": "q10_pqq_spermidine",
        "name": "Q10 + PQQ + Spermidyna (combo)",
        "default_dose": {
            "amount": None,
            "unit": None,
            "timing_hint": "morning",
        },
        "tags": {"MITO", "NAD"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "q10pqqsperm_5on2off",
                "type": "week_pattern",
                "active_blocks": {"MITO", "NAD"},
                "params": {"days_included": {0, 1, 2, 3, 4}},
            }
        ],
        "priority": 60,  # możesz zostawić 60 jak q10 albo 55 jak pqq
        "notes": "W NAD obejmuje też Q10 z racji produktu 3w1.",
    },
    # "q10": {
    #    "id": "q10",
    #    "name": "Q10",
    #    "default_dose": {
    #        "amount": None,
    #        "unit": None,
    #        "timing_hint": "morning",
    #    },
    #    "tags": {"MITO"},
    #    "constraints": [],
    #    "schedule_rules": [
    #        {
    #            "id": "q10_5on2off",
    #            "type": "week_pattern",
    #            "active_blocks": {"MITO"},
    #            "params": {"days_included": {0, 1, 2, 3, 4}},
    #        }
    #    ],
    #    "priority": 60,
    #    "notes": None,
    # },
    # "pqq": {
    #    "id": "pqq",
    #    "name": "PQQ",
    #    "default_dose": {
    #        "amount": None,
    #        "unit": None,
    #        "timing_hint": "morning",
    #    },
    #    "tags": {"MITO", "NAD"},
    #    "constraints": [],
    #    "schedule_rules": [
    #        {
    #            "id": "pqq_5on2off",
    #            "type": "week_pattern",
    #            "active_blocks": {"MITO", "NAD"},
    #            "params": {"days_included": {0, 1, 2, 3, 4}},
    #        }
    #    ],
    #    "priority": 55,
    #    "notes": None,
    # },
    # "spermidine": {
    #    "id": "spermidine",
    #    "name": "Spermidyna",
    #    "default_dose": None,
    #    "tags": {"MITO", "NAD"},
    #    "constraints": [],
    #    "schedule_rules": [
    #        {
    #            "id": "sperm_5on2off",
    #            "type": "week_pattern",
    #            "active_blocks": {"MITO", "NAD"},
    #            "params": {"days_included": {0, 1, 2, 3, 4}},
    #        }
    #    ],
    #    "priority": 50,
    #    "notes": None,
    # },
    "cordyceps": {
        "id": "cordyceps",
        "name": "Cordyceps",
        "default_dose": {
            "amount": None,
            "unit": None,
            "timing_hint": "morning",
        },
        "tags": {"MITO"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "cordyceps_4x",
                "type": "times_per_week",
                "active_blocks": {"MITO"},
                "params": {
                    "n": 4,
                    "selection_policy": "fixed_days",
                    "fixed_days": [0, 2, 3, 5],
                },
            }
        ],
        "priority": 35,
        "notes": None,
    },
    "astaxanthin": {
        "id": "astaxanthin",
        "name": "Astaksantyna",
        "default_dose": None,
        "tags": {"MITO"},
        "constraints": [],
        "schedule_rules": [
            # MITO: codziennie
            {
                "id": "astax_daily_mito",
                "type": "daily",
                "active_blocks": {"MITO"},
                "params": {},
            },
            # POZA MITO: 3x/tydz (ale nie NAD)
            {
                "id": "astax_3x_else",
                "type": "times_per_week",
                "active_blocks": {"ANTIAGE", "DETOX"},
                "params": {
                    "n": 3,
                    "selection_policy": "fixed_days",
                    "fixed_days": [0, 2, 4],  # Mon/Wed/Fri
                },
            },
        ],
        "priority": 30,
        "notes": None,
    },
    "gotu_kola": {
        "id": "gotu_kola",
        "name": "Gotu Kola",
        "default_dose": None,
        "tags": {"MITO", "DETOX"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "gotu_5on2off",
                "type": "week_pattern",
                "active_blocks": {"MITO", "DETOX"},
                "params": {"days_included": {0, 1, 2, 3, 4}},
            }
        ],
        "priority": 30,
        "notes": None,
    },
    # ANTI-AGE
    "r_ala": {
        "id": "r_ala",
        "name": "R-ALA",
        "default_dose": {
            "amount": None,
            "unit": None,
            "timing_hint": "morning",
        },
        "tags": {"ANTIAGE"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "rala_5on2off",
                "type": "week_pattern",
                "active_blocks": {"ANTIAGE"},
                "params": {"days_included": {0, 1, 2, 3, 4}},
            }
        ],
        "priority": 55,
        "notes": None,
    },
    "benfotiamine": {
        "id": "benfotiamine",
        "name": "Benfotiamina",
        "default_dose": None,
        "tags": {"ANTIAGE"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "benfo_daily",
                "type": "daily",
                "active_blocks": {"ANTIAGE"},
                "params": {},
            }
        ],
        "priority": 45,
        "notes": None,
    },
    "carnosine": {
        "id": "carnosine",
        "name": "L-karnozyna",
        "default_dose": None,
        "tags": {"ANTIAGE"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "carno_daily",
                "type": "daily",
                "active_blocks": {"ANTIAGE"},
                "params": {},
            }
        ],
        "priority": 45,
        "notes": None,
    },
    "berberine": {
        "id": "berberine",
        "name": "Berberyna",
        "default_dose": None,
        "tags": {"ANTIAGE"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "berb_3on",
                "type": "week_pattern",
                "active_blocks": {"ANTIAGE"},
                "params": {"days_included": {0, 2, 4}},
            }
        ],
        "priority": 40,
        "notes": None,
    },
    "curcumin_piperine": {
        "id": "curcumin_piperine",
        "name": "Kurkumina + piperyna",
        "default_dose": None,
        "tags": {"ANTIAGE"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "curc_daily",
                "type": "daily",
                "active_blocks": {"ANTIAGE"},
                "params": {},
            }
        ],
        "priority": 50,
        "notes": None,
    },
    "lycopene": {
        "id": "lycopene",
        "name": "Likopen",
        "default_dose": None,
        "tags": {"ANTIAGE"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "lyco_daily",
                "type": "daily",
                "active_blocks": {"ANTIAGE"},
                "params": {},
            }
        ],
        "priority": 45,
        "notes": None,
    },
    "opc": {
        "id": "opc",
        "name": "OPC",
        "default_dose": None,
        "tags": {"ANTIAGE"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "opc_daily_antiage",
                "type": "daily",
                "active_blocks": {"ANTIAGE"},
                "params": {},
            },
            {
                "id": "opc_3x_else",
                "type": "times_per_week",
                "active_blocks": {"NAD", "MITO", "DETOX"},
                "params": {
                    "n": 3,
                    "selection_policy": "fixed_days",
                    "fixed_days": [0, 2, 4],
                },
            },
        ],
        "priority": 35,
        "notes": None,
    },
    "beet_extract": {
        "id": "beet_extract",
        "name": "Ekstrakt z buraka",
        "default_dose": None,
        "tags": {"ANTIAGE"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "beet_4x",
                "type": "times_per_week",
                "active_blocks": {"ANTIAGE"},
                "params": {
                    "n": 4,
                    "selection_policy": "fixed_days",
                    "fixed_days": [0, 2, 4, 5],
                },
            }
        ],
        "priority": 25,
        "notes": None,
    },
    "hawthorn": {
        "id": "hawthorn",
        "name": "Ekstrakt z głogu",
        "default_dose": None,
        "tags": {"ANTIAGE"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "hawthorn_daily",
                "type": "daily",
                "active_blocks": {"ANTIAGE"},
                "params": {},
            }
        ],
        "priority": 25,
        "notes": None,
    },
    "aronia_c": {
        "id": "aronia_c",
        "name": "Aronia + witamina C",
        "default_dose": None,
        "tags": {"ANTIAGE", "MITO"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "aronia_daily",
                "type": "daily",
                "active_blocks": {"ANTIAGE", "MITO"},
                "params": {},
            }
        ],
        "priority": 25,
        "notes": None,
    },
    "saw_palmetto": {
        "id": "saw_palmetto",
        "name": "Palma sabałowa",
        "default_dose": None,
        "tags": {"ANTIAGE"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "sawp_3x",
                "type": "times_per_week",
                "active_blocks": {"ANTIAGE"},
                "params": {
                    "n": 3,
                    "selection_policy": "fixed_days",
                    "fixed_days": [0, 2, 4],
                },
            }
        ],
        "priority": 20,
        "notes": None,
    },
    # DETOX
    "nac": {
        "id": "nac",
        "name": "NAC",
        "default_dose": None,
        "tags": {"DETOX"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "nac_5on2off",
                "type": "week_pattern",
                "active_blocks": {"DETOX"},
                "params": {"days_included": {0, 1, 2, 3, 4}},
            }
        ],
        "priority": 60,
        "notes": None,
    },
    "selenium": {
        "id": "selenium",
        "name": "Selen",
        "default_dose": None,
        "tags": {"DETOX"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "sel_same_as_nac",
                "type": "week_pattern",
                "active_blocks": {"DETOX"},
                "params": {"days_included": {0, 1, 2, 3, 4}},
            }
        ],
        "priority": 55,
        "notes": "Razem z NAC (produkt łączony).",
    },
    "silymarin": {
        "id": "silymarin",
        "name": "Sylimaryna",
        "default_dose": None,
        "tags": {"DETOX"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "sily_daily",
                "type": "daily",
                "active_blocks": {"DETOX"},
                "params": {},
            }
        ],
        "priority": 35,
        "notes": None,
    },
    "lecithin_sunflower": {
        "id": "lecithin_sunflower",
        "name": "Lecytyna słonecznikowa",
        "default_dose": None,
        "tags": {"DETOX"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "lec_4x",
                "type": "times_per_week",
                "active_blocks": {"DETOX"},
                "params": {
                    "n": 4,
                    "selection_policy": "fixed_days",
                    "fixed_days": [0, 2, 3, 5],
                },
            }
        ],
        "priority": 25,
        "notes": None,
    },
    "fitolizyna": {
        "id": "fitolizyna",
        "name": "Fitolizyna",
        "default_dose": None,
        "tags": {"DETOX"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "fito_daily",
                "type": "daily",
                "active_blocks": {"DETOX"},
                "params": {},
            }
        ],
        "priority": 25,
        "notes": None,
    },
    "chanca_piedra": {
        "id": "chanca_piedra",
        "name": "Chanca Piedra",
        "default_dose": None,
        "tags": {"DETOX"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "chanca_daily",
                "type": "daily",
                "active_blocks": {"DETOX"},
                "params": {},
            }
        ],
        "priority": 25,
        "notes": None,
    },
    "melissa": {
        "id": "melissa",
        "name": "Melisa",
        "default_dose": {
            "amount": None,
            "unit": None,
            "timing_hint": "evening",
        },
        "tags": {"DETOX"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "mel_optional",
                "type": "optional",
                "active_blocks": {"DETOX"},
                "params": {"flag": "enable_melissa"},
            }
        ],
        "priority": 5,
        "notes": None,
    },
    "ashwagandha": {
        "id": "ashwagandha",
        "name": "Ashwagandha",
        "default_dose": {
            "amount": None,
            "unit": None,
            "timing_hint": "evening",
        },
        "tags": {"DETOX", "ANTIAGE"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "ash_cycle_8_4",
                "type": "cycle_weeks",
                "active_blocks": {"DETOX", "ANTIAGE"},
                "params": {
                    "on_weeks": 8,
                    "off_weeks": 4,
                    "alignment": "custom_date",
                },
            }
        ],
        "priority": 30,
        "notes": None,
    },
    # NEURO
    "l_theanine": {
        "id": "l_theanine",
        "name": "L-teanina",
        "default_dose": {
            "amount": None,
            "unit": None,
            "timing_hint": "evening",
        },
        "tags": {"NEURO"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "theanine_daily",
                "type": "daily",
                "active_blocks": None,
                "params": {},
            }
        ],
        "priority": 20,
        "notes": None,
    },
    "apigenin": {
        "id": "apigenin",
        "name": "Apigenina",
        "default_dose": {
            "amount": None,
            "unit": None,
            "timing_hint": "evening",
        },
        "tags": {"NEURO"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "apigenin_daily",
                "type": "daily",
                "active_blocks": None,
                "params": {},
            }
        ],
        "priority": 20,
        "notes": None,
    },
    "l_tyrosine": {
        "id": "l_tyrosine",
        "name": "L-tyrozyna",
        "default_dose": {
            "amount": None,
            "unit": None,
            "timing_hint": "morning",
        },
        "tags": {"NEURO"},
        "constraints": [
            {
                "id": "tyr_exclude_blocks_detox",
                "type": "exclude_blocks",
                "params": {"blocks": {"DETOX"}},
            }
        ],
        "schedule_rules": [
            {
                "id": "tyr_2x_week",
                "type": "times_per_week",
                "active_blocks": None,
                "params": {
                    "n": 2,
                    "selection_policy": "fixed_days",
                    "fixed_days": [1, 3],
                    "weekdays_only": True,
                },
            }
        ],
        "priority": 15,
        "notes": None,
    },
    "ginkgo": {
        "id": "ginkgo",
        "name": "Ginkgo biloba",
        "default_dose": {
            "amount": None,
            "unit": None,
            "timing_hint": "morning",
        },
        "tags": {"NEURO"},
        "constraints": [
            {
                "id": "ginkgo_exclude_blocks_nad",
                "type": "exclude_blocks",
                "params": {"blocks": {"NAD"}},
            }
        ],
        "schedule_rules": [
            {
                "id": "ginkgo_3x",
                "type": "times_per_week",
                "active_blocks": None,
                "params": {
                    "n": 3,
                    "selection_policy": "fixed_days",
                    "fixed_days": [0, 2, 4],
                },
            }
        ],
        "priority": 15,
        "notes": None,
    },
    # FISETYNA (event-driven)
    "fisetin_pulse": {
        "id": "fisetin_pulse",
        "name": "Fisetyna",
        "default_dose": {
            "amount": 12,
            "unit": "caps",
            "timing_hint": "morning",
        },
        "tags": {"PULSE"},
        "constraints": [],
        "schedule_rules": [
            {
                "id": "fisetin_event_only",
                "type": "event_only",
                "active_blocks": None,
                "params": {"event_id": "pulse_fisetin"},
            }
        ],
        "priority": 1000,
        "notes": None,
    },
}

# =========================
# SCHEMATY (twarde)
# =========================

COMMON_SCHEMAS = {
    "active_blocks": {
        "type": "None|set[str]|list[str]",
        "nonempty_if_not_none": True,
        "values_must_be_in": "BLOCKS.keys()",
        "normalization": "sorted_list_or_none",
    },
    "id": {"type": "str", "nonempty": True},
    "type": {"type": "str", "nonempty": True},
}

SCHEDULE_RULE_TYPES = {
    "__common__": {
        "required_fields": {"id", "type", "active_blocks", "params"},
        "field_schemas": {
            "id": COMMON_SCHEMAS["id"],
            "type": COMMON_SCHEMAS["type"],
            "active_blocks": COMMON_SCHEMAS["active_blocks"],
            "params": {"type": "dict"},
        },
        "enforce_no_extra_top_level_fields": True,
        "enforce_params_allowed_only": True,
    },
    "daily": {
        "required_fields": {"id", "type", "active_blocks", "params"},
        "params_required": set(),
        "params_allowed": set(),
    },
    "week_pattern": {
        "required_fields": {"id", "type", "active_blocks", "params"},
        "params_required": {"days_included"},
        "params_allowed": {"days_included"},
        "params_schema": {
            "days_included": {
                "type": "set[int]|list[int]",
                "allowed_range": [0, 6],
                "nonempty": True,
                "normalization": "sorted_list",
            },
        },
    },
    "times_per_week": {
        "required_fields": {"id", "type", "active_blocks", "params"},
        "params_required": {"n", "selection_policy", "fixed_days"},
        "params_allowed": {
            "n",
            "selection_policy",
            "fixed_days",
            "weekdays_only",
        },
        "params_schema": {
            "n": {"type": "int", "min": 1, "max": 7},
            "selection_policy": {"type": "enum", "values": {"fixed_days"}},
            "fixed_days": {
                "type": "list[int]|set[int]",
                "allowed_range": [0, 6],
                "len_min": 1,
                "len_max": 7,
                "normalization": "sorted_list",
            },
            "weekdays_only": {"type": "bool"},
        },
    },
    "cycle_weeks": {
        "required_fields": {"id", "type", "active_blocks", "params"},
        "params_required": {"on_weeks", "off_weeks", "alignment"},
        "params_allowed": {"on_weeks", "off_weeks", "alignment"},
        "params_schema": {
            "on_weeks": {"type": "int", "min": 1, "max": 52},
            "off_weeks": {"type": "int", "min": 1, "max": 52},
            "alignment": {
                "type": "enum",
                "values": {"year_start", "custom_date"},
            },
        },
    },
    "optional": {
        "required_fields": {"id", "type", "active_blocks", "params"},
        "params_required": {"flag"},
        "params_allowed": {"flag"},
        "params_schema": {"flag": {"type": "str", "nonempty": True}},
    },
    "event_only": {
        "required_fields": {"id", "type", "active_blocks", "params"},
        "params_required": {"event_id"},
        "params_allowed": {"event_id"},
        "params_schema": {"event_id": {"type": "str", "nonempty": True}},
    },
}

CONSTRAINT_TYPES = {
    "__common__": {
        "required_fields": {"id", "type", "params"},
        "field_schemas": {
            "id": COMMON_SCHEMAS["id"],
            "type": COMMON_SCHEMAS["type"],
            "params": {"type": "dict"},
        },
        "enforce_no_extra_top_level_fields": True,
        "enforce_params_allowed_only": True,
    },
    "exclude_blocks": {
        "required_fields": {"id", "type", "params"},
        "params_required": {"blocks"},
        "params_allowed": {"blocks"},
        "params_schema": {
            "blocks": {
                "type": "set[str]|list[str]",
                "nonempty": True,
                "values_must_be_in": "BLOCKS.keys()",
                "normalization": "sorted_list",
            }
        },
    },
    "allowed_blocks": {
        "required_fields": {"id", "type", "params"},
        "params_required": {"blocks"},
        "params_allowed": {"blocks"},
        "params_schema": {
            "blocks": {
                "type": "set[str]|list[str]",
                "nonempty": True,
                "values_must_be_in": "BLOCKS.keys()",
                "normalization": "sorted_list",
            }
        },
    },
    "exclude_supplements": {
        "required_fields": {"id", "type", "params"},
        "params_required": {"supplement_ids"},
        "params_allowed": {"supplement_ids"},
        "params_schema": {
            "supplement_ids": {
                "type": "set[str]|list[str]",
                "nonempty": True,
                "values_must_be_in": "SUPPLEMENTS.keys()",
                "normalization": "sorted_list",
            }
        },
    },
    "require_supplements": {
        "required_fields": {"id", "type", "params"},
        "params_required": {"supplement_ids"},
        "params_allowed": {"supplement_ids"},
        "params_schema": {
            "supplement_ids": {
                "type": "set[str]|list[str]",
                "nonempty": True,
                "values_must_be_in": "SUPPLEMENTS.keys()",
                "normalization": "sorted_list",
            }
        },
    },
    "seasonal": {
        "required_fields": {"id", "type", "params"},
        "params_required": {"months_included"},
        "params_allowed": {"months_included"},
        "params_schema": {
            "months_included": {
                "type": "set[int]|list[int]",
                "allowed_range": [1, 12],
                "nonempty": True,
                "normalization": "sorted_list",
            }
        },
    },
}

EVENT_TYPES = {
    "pulse": {
        "required_fields": {
            "id",
            "type",
            "months",
            "length_days",
            "month_week_selection",
            "time_of_day",
            "override_id",
            "priority",
            "capsules_per_day",
        },
        "months_schema": {
            "type": "list[int]",
            "allowed_range": [1, 12],
            "nonempty": True,
        },
        "length_days_schema": {"type": "int", "min": 1, "max": 14},
        "month_week_selection_schema": {"type": "int", "min": 1, "max": 5},
        "time_of_day_schema": {
            "type": "enum",
            "values": {"morning", "evening", "any"},
        },
        "capsules_per_day_schema": {"type": "int", "min": 1, "max": 40},
    }
}

VALIDATION = {
    "ids": {
        "supplement_id_format": "^[a-z0-9_]+$",
        "block_ids_allowed": set(BLOCKS.keys()),
        "schedule_rule_types_allowed": set(SCHEDULE_RULE_TYPES.keys()),
        "constraint_types_allowed": set(CONSTRAINT_TYPES.keys()),
        "event_types_allowed": set(EVENT_TYPES.keys()),
    },
    "cross_refs": {
        "schedule_rules_event_only_event_id_must_exist_in_EVENTS": True,
        "event_override_id_must_exist_in_CONFLICTS_event_overrides": True,
        "core_set_ids_must_exist_in_SUPPLEMENTS": True,
        "block_calendar_months_must_be_1_12": True,
        "block_calendar_values_must_exist_in_BLOCKS": True,
        "constraints_must_match_constraint_type_schema": True,
        "schedule_rules_must_match_rule_type_schema": True,
        "events_must_match_event_type_schema": True,
        "active_blocks_must_reference_existing_BLOCKS": True,
        "week_pattern_days_included_must_be_weekday_indices": True,
        "times_per_week_fixed_days_must_be_weekday_indices": True,
    },
    "consistency": {
        "pipeline_required": True,
        "off_week_must_not_overlap_with_events": {
            "off_week": {"pulse_fisetin"}
        },
        "supplement_exclusions_policy_required": True,
        "supplement_exclusions_policy_apply_phase_allowed": {
            "apply_supplement_exclusions"
        },
        "supplement_exclusions_policy_direction_allowed": {"one_way"},
        "pipeline_must_equal": [
            "base_by_block",
            "apply_schedule_rules",
            "apply_constraints",
            "apply_supplement_exclusions",
            "apply_block_exclusions",
            "apply_events",
            "apply_global_exceptions",
        ],
    },
    "normalization": {
        "accept_set_inputs": True,
        "normalize_sets_to_sorted_lists": True,
    },
}

NORMALIZATION_RULES = {
    "collections": {
        "active_blocks": "None|set|list -> None|sorted_list",
        "week_pattern.params.days_included": "set|list -> sorted_list",
        "times_per_week.params.fixed_days": "set|list -> sorted_list",
        "constraint.params.blocks": "set|list -> sorted_list",
        "constraint.params.supplement_ids": "set|list -> sorted_list",
        "constraint.params.months_included": "set|list -> sorted_list",
        "core_set": "set -> sorted_list (opcjonalnie, do determ. porównań)",
    },
    "ordering": {
        "day_items_sort": [
            "timing_hint",
            "priority_desc",
            "supplement_id_asc",
        ],
        "timing_hint_order": ["morning", "any", "evening", None],
    },
}

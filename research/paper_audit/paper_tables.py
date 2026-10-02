"""Transcription of Al-Rasheed et al., IEEE Trans. Consum. Electron. 72(2), May 2026
(docs/base_paper.pdf). Transcribed from a 300-DPI render of PDF pages 6-8 (journal pp. 4488-4490).
Every cell below was read from the rendered table, not from extracted text."""

# Table III (p.4488): reference processing times, ms
T3 = {"ECM": 17.1, "C": 0.32, "SE/D": 5.6, "H": 0.32, "fe": 17.1}

# Table V (p.4489): operation counts per role. keys: H, SE/D, ECM, fe. None = "—".
T5 = {
    "Proposed scheme":     {"user": None,                                  "device": {"H": 2, "SE/D": 2},            "server": {"H": 2, "SE/D": 2}},
    "Challa et al. [17]":  {"user": {"fe": 1, "H": 5, "SE/D": 5},          "device": {"H": 3, "ECM": 4},             "server": {"H": 4, "ECM": 5}},
    "Turkanovic [12]":     {"user": {"H": 7},                              "device": {"H": 7},                       "server": {"H": 5}},
    "Poorambage [11]":     {"user": {"H": 8, "ECM": 4},                    "device": {"H": 10, "ECM": 11},           "server": {"H": 5, "ECM": 8}},
    "Dhillon-Karla [13]":  {"user": {"H": 8},                              "device": {"H": 6},                       "server": {"H": 8}},
    "Cheng-Le [14]":       {"user": {"H": 9, "ECM": 2},                    "device": {"H": 5, "ECM": 2},             "server": {"H": 7}},
    "Shuai [16]":          {"user": {"H": 6, "ECM": 1},                    "device": {"H": 3, "ECM": 1},             "server": {"H": 7, "ECM": 1}},
    "Jiang [15]":          {"user": {"H": 7},                              "device": {"H": 5},                       "server": {"H": 10}},
    "Wazid [17]":          {"user": {"fe": 1, "H": 13, "SE/D": 2},         "device": {"H": 4, "SE/D": 2},            "server": {"H": 5, "SE/D": 4}},
    "Sadhukhan [18]":      {"user": {"H": 2, "ECM": 1, "SE/D": 2},         "device": {"H": 1, "ECM": 1, "SE/D": 2},  "server": {"H": 2, "SE/D": 4}},
}

# Table IV (p.4489): communication cost in bits. (messages, user, device, server, total)
T4 = {
    "Proposed scheme": (4, None, 512, 512, 1024),
    "Poorambage [11]": (4, 768, 768, 1824, 3360),
    "Turkanovic [12]": (4, 672, 576, 1472, 2720),
    "Dhillon-Karla [13]": (4, 992, 512, 1024, 2528),
    "Cheng-Le [14]": (4, 672, 512, 1088, 2272),
    "Jiang [15]": (4, 512, 1056, 384, 1952),
    "Shuai [16]": (4, 864, 544, 960, 2368),
    "Wazid [17]": (4, 736, 512, 1344, 2592),
    "Sadhukhan [18]": (4, 320, 768, 512, 1600),
    "Fakroon [19]": (4, 800, 416, 1088, 2304),
}

# Table VI (p.4490), captioned "Comparative analysis of the communication cost" (sic) but it is storage. bits.
T6 = {
    "Proposed scheme": (320, 320),
    "Turkanovic [12]": (768, 512),
    "Dhillon-Karla [13]": (640, 512),
    "Wazid [17]": (576, 512),
    "Sadhukhan [18]": (480, 356),
    "Fakroon [19]": (704, 1056),
    # Das et al. [20]: server 768 + CH* (undefined), device "-" -> excluded
}

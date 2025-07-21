import json
from typing import TypedDict, NotRequired


class Conditions(TypedDict):
    condition_on: list[str]
    type: str
    matches: list[str]


class Rules(TypedDict):
    role: str
    priority: int
    patterns: list[list[str]]
    conditions: NotRequired[Conditions]
    description: str


class Role(TypedDict):
    name: str
    description: str
    type: NotRequired[str]
    role: NotRequired[str]


class SyntacticGroup(TypedDict):
    span: list[tuple[str, str]]
    role: str
    description: str
    priority: int


with open("data/grammar/josa.json", "r") as f:
    josa = json.load(f)

with open("data/grammar/korean_syntactic_grouping_rules.json", "r") as f:
    rules = json.load(f)

with open("data/grammar/korean_pos_tags.json", "r") as f:
    pos_tags = json.load(f)


def evaluate_conditions(word: str, role: str, type: str, matches: list[str]) -> bool:
    if role == "negation":
        condition_template = f"'{word + '다'}'%'match'"
    else:
        condition_template = f"'{word}'%'match'"
    if type == "=":
        condition_template = condition_template.replace("%", "==")
    elif type == "end":
        condition_template = condition_template.replace("%", ".endswith(") + ")"

    for match in matches:
        condition = condition_template.replace("match", match)
        if eval(condition):
            return True
    return False


def grammatical_identification(
    tokens: list[tuple[str, str]],
) -> list[tuple[str, str, Role]]:
    res = []
    for word, pos in tokens:
        role = dict()
        if pos in pos_tags:
            role.update(pos_tags[pos])
            # Josa, additional info
            if pos in ["JX", "JC", "JKQ", "JKV", "JKB", "JKO", "JKG", "JKC", "JKS"]:
                for key in josa:
                    if word in key:
                        role.update(josa[key])
        else:
            role = None
        res.append((word, pos, role))
    return res


def syntactic_grouping(
    tokens: list[tuple[str, str]], rules: Rules
) -> list[SyntacticGroup]:
    syntactic_groups = []
    sorted_rules = sorted(rules, key=lambda r: r["priority"])
    used_indices = set()

    for rule in sorted_rules:
        if "conditions" in rule:
            conditions = rule["conditions"]
        else:
            conditions = None
        for pattern in rule["patterns"]:
            window_size = len(pattern)
            for i in range(len(tokens) - window_size + 1):
                if any((i + j) in used_indices for j in range(window_size)):
                    continue
                token_window = tokens[i : i + window_size]
                pos_sequence = [pos for _, pos in token_window]

                if pos_sequence == pattern:
                    if conditions:
                        for index, pos in enumerate(pos_sequence):
                            if pos in conditions["on"] and evaluate_conditions(
                                token_window[index][0],
                                rule["role"],
                                conditions["type"],
                                conditions["matches"],
                            ):
                                syntactic_groups.append(
                                    {
                                        "span": token_window,
                                        "role": rule["role"],
                                        "description": rule["description"],
                                        "priority": rule["priority"],
                                    }
                                )
                                break
                    else:
                        syntactic_groups.append(
                            {
                                "span": token_window,
                                "role": rule["role"],
                                "description": rule["description"],
                                "priority": rule["priority"],
                            }
                        )

                    used_indices.update(range(i, i + window_size))
                    break
    return syntactic_groups


tokens = [
    ("학생", "NNG"),  # student
    ("이", "JKS"),  # subject marker
    ("학교", "NNG"),  # school
    ("에", "JKB"),  # locative
    ("가", "VV"),  # go
    ("지", "EC"),  # connective
    ("않", "VX"),  # negation
    ("을", "EP"),  # pre-final ending
    ("까요", "EF"),  # interrogative polite ending
]

results = syntactic_grouping(tokens, rules)
for match in results:
    print(f"{match['role'].upper()} → {[form for form, _ in match['span']]}")

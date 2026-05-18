HUMANIZED_ENUMERATION_PROJECT = {
    1: "проект",
    2: "проекта",
    3: "проекта",
    4: "проекта",
    5: "проектов",
    6: "проектов",
    7: "проектов",
    8: "проектов",
    9: "проектов",
    0: "проектов",
}


def get_humanized_enumeration_project(number: int):
    return HUMANIZED_ENUMERATION_PROJECT.get(number % 10)

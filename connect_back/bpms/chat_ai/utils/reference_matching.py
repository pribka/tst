import re


def normalize_name_text(value):
    text = str(value or "").lower()
    text = text.replace("\u0451", "\u0435")
    text = re.sub(r"[^0-9a-z\u0430-\u044f\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def name_tokens(value):
    text = normalize_name_text(value)
    return [token for token in text.split(" ") if token]


def token_stem(token):
    token = (token or "").strip()
    if len(token) <= 5:
        return token
    return token[:5]


def split_reference_names(raw_value, model_path=""):
    text = str(raw_value or "").strip()
    if not text:
        return []

    if model_path == "users.ProfileModel":
        chunks = re.split(r"(?:,|;|\n|\s+\b\u0438\b\s+)", text, flags=re.IGNORECASE)
    else:
        chunks = re.split(r"(?:,|;|\n)", text)

    names = []
    seen = set()
    for chunk in chunks:
        name = re.sub(r"^[\W_]+|[\W_]+$", "", (chunk or "").strip())
        if not name:
            continue
        key = normalize_name_text(name)
        if key in seen:
            continue
        seen.add(key)
        names.append(name)
    return names


def _candidate_identity(candidate):
    if not isinstance(candidate, dict):
        return None
    return str(candidate.get("id") or candidate.get("pk") or candidate.get("repr") or "")


def _candidate_score(requested_name, candidate):
    if not isinstance(candidate, dict):
        return None

    requested_tokens = name_tokens(requested_name)
    if not requested_tokens:
        return None
    requested_stems = [token_stem(token) for token in requested_tokens]

    candidate_repr = candidate.get("repr") or ""
    candidate_tokens = name_tokens(candidate_repr)
    if not candidate_tokens:
        return None
    candidate_stems = {token_stem(token) for token in candidate_tokens}

    matches = sum(1 for stem in requested_stems if stem in candidate_stems)
    if matches != len(requested_stems):
        return None

    # Чем меньше "лишних" токенов у кандидата относительно запроса, тем лучше.
    exact_match = int(normalize_name_text(candidate_repr) == normalize_name_text(requested_name))
    extra_tokens = max(0, len(candidate_tokens) - len(requested_tokens))
    return exact_match, -extra_tokens, -len(candidate_tokens)


def pick_best_candidate(requested_name, candidates):
    if not isinstance(candidates, list) or not candidates:
        return None

    # Дедупликация по id/pk/repr.
    uniq = []
    seen = set()
    for candidate in candidates:
        key = _candidate_identity(candidate)
        if not key or key in seen:
            continue
        seen.add(key)
        uniq.append(candidate)

    scored = []
    for candidate in uniq:
        score = _candidate_score(requested_name, candidate)
        if score is None:
            continue
        scored.append((score, candidate))

    if not scored:
        return None

    scored.sort(key=lambda item: item[0], reverse=True)
    top_score = scored[0][0]
    top_candidates = [candidate for score, candidate in scored if score == top_score]

    # Если лидер не единственный, считаем сопоставление неоднозначным.
    if len(top_candidates) != 1:
        return None
    return top_candidates[0]


def match_reference_candidates(candidates, requested_names, many=False, model_path=""):
    if isinstance(requested_names, str):
        names = split_reference_names(requested_names, model_path)
    else:
        names = []
        for item in (requested_names or []):
            value = str(item or "").strip()
            if value:
                names.append(value)

    if not names or not isinstance(candidates, list) or not candidates:
        return []

    grouped_exact = {}
    grouped_norm = {}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        for_name = str(candidate.get("for_name") or "").strip()
        if for_name:
            grouped_exact.setdefault(for_name, []).append(candidate)
            grouped_norm.setdefault(normalize_name_text(for_name), []).append(candidate)

    selected = []
    selected_keys = set()
    for name in names:
        name_candidates = (
            grouped_exact.get(name)
            or grouped_norm.get(normalize_name_text(name))
            or candidates
        )
        picked = pick_best_candidate(name, name_candidates)
        if not picked:
            continue
        key = _candidate_identity(picked)
        if not key or key in selected_keys:
            continue
        selected_keys.add(key)
        selected.append(picked)
        if not many:
            break

    return selected


def resolve_reference_field_value(raw_value, model_path, field_type, candidates):
    names = split_reference_names(raw_value, model_path)
    if not names:
        return [] if field_type == "ManyToManyField" else None

    if field_type in ["ForeignKey", "OneToOneField"]:
        if len(names) != 1:
            return None
        picked = match_reference_candidates(candidates, names[0], many=False, model_path=model_path)
        if not picked:
            return None
        return {k: v for k, v in picked[0].items() if k != "for_name"}

    if field_type == "ManyToManyField":
        selected = match_reference_candidates(candidates, names, many=True, model_path=model_path)
        return [{k: v for k, v in item.items() if k != "for_name"} for item in selected]

    return None


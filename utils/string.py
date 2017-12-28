def boyer_moore_horspool(string, pat, start_idx=0, max_match=-1):
    return boyer_moore_horspool_heur(string, pat, _bad_char_heuristic(pat), start_idx, max_match)


def boyer_moore_horspool_heur(string, pat, heur, start_idx=0, max_match=-1):
    match_idx = []

    sLen = len(string)
    patLen = len(pat)
    match_cnt = 0

    i = patLen - 1 + start_idx
    while (max_match < 0 or match_cnt < max_match) and i < sLen:
        j = i
        pat_idx = patLen - 1
        while pat[pat_idx] == string[j] and pat_idx >= 0:
            j -= 1
            pat_idx -= 1

        matched = False

        if pat_idx == -1:
            # record match
            match_idx.append(j + 1)
            matched = True
            match_cnt += 1

        h = heur[string[i]] if string[i] in heur else -1

        if matched or h == -1:
            i += patLen
        else:
            # get shift distance
            i += patLen - 1 - h

    return match_idx


def _bad_char_heuristic(pat):
    last_f = {}

    for i in range(0, len(pat) - 1):
        last_f[pat[i]] = i

    return last_f


def get_end_of_code_sequence(in_code, start_idx):
    open_brace = -1
    end_idx = start_idx

    while open_brace == -1 or open_brace > 0:
        if in_code[end_idx] == '{':
            open_brace = 1 if open_brace == -1 else open_brace + 1
        elif in_code[end_idx] == '}':
            open_brace -= 1

        end_idx += 1
    return end_idx

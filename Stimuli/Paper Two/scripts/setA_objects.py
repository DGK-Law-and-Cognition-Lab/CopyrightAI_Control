"""Object-position check for Set A (amendment of 29 October 2026; supersedes the spill check).

Tracked objects per scene, fixed before any judging:
- the noun chunks (spaCy en_core_web_sm) of the scene's Composition and Background sentences in the bank;
- each chunk's head noun (its root token, when the root is a noun), lemmatized to the singular, as the detector
  query "a" or "an" + noun ("an" before a vowel letter);
- excluded: the scene's added elements at all three amounts (the head noun of each element phrase's first noun
  chunk, and the noun of the element's detector query); the person or people of the Subject sentence (the head
  noun of the Subject sentence's first noun chunk, in a scene with a person); and the fixed list of surfaces and
  regions in SURFACES.
A tracked object is trackable when the detector finds it in the accepted source at or above the score cut;
otherwise it is untrackable and ignored.

The check: for every trackable object that the detector finds in the file's input at or above the cut (its best
box there), the composited file must have a box for the same query at or above the cut whose intersection over
union with that input box is at least IOU_MIN (the best-matching box is used). The input is the accepted source for
small and medium, and the accepted medium file for large.
"""

import spacy

import setA_common as C
import setA_checks as K

SURFACES = {"table", "floor", "wall", "rug", "ground", "sky", "sea", "water", "river", "field", "street", "road",
            "room", "frame", "end", "area", "stretch", "side", "corner", "center", "centre", "left", "right",
            "third", "foreground", "background", "distance", "horizon"}
IOU_MIN = 0.5   # fixed constant, not tuned
_nlp = None


def nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def head_lemma(text):
    chunks = list(nlp()(text).noun_chunks)
    if not chunks or chunks[0].root.pos_ not in ("NOUN", "PROPN"):
        return None
    return chunks[0].root.lemma_.lower()


def query(noun):
    return ("an " if noun[0] in "aeiou" else "a ") + noun


def tracked_objects(scene):
    """{"tracked": [queries], "excluded": {noun: reason}} for one scene, from the bank's sentences."""
    parts = dict(zip(C.PARTS, scene["parts"]))
    excluded, nouns = {}, []
    for part in ("Composition", "Background"):
        for ch in nlp()(parts[part]).noun_chunks:
            if ch.root.pos_ not in ("NOUN", "PROPN"):
                continue
            n = ch.root.lemma_.lower()
            if n not in nouns:
                nouns.append(n)
    added = set()
    for e in [scene["small"], scene["medium"]] + scene["large_elements"]:
        h = head_lemma(e)
        if h:
            added.add(h)
        added.add(C.ELEMENT_QUERIES[e].split()[-1])                     # the query's noun (last word)
        added.add(nlp()(C.ELEMENT_QUERIES[e])[-1].lemma_.lower())        # and its singular ("reeds" -> "reed")
    person = head_lemma(parts["Subject"]) if scene["person"] else None
    tracked = []
    for n in nouns:
        if n in SURFACES:
            excluded[n] = "surface or region"
        elif n in added:
            excluded[n] = "added element"
        elif person and n == person:
            excluded[n] = "person of the Subject sentence"
        else:
            tracked.append(query(n))
    return {"tracked": tracked, "excluded": excluded, "nouns": nouns}


def best_box(boxes, cut):
    ok = [b for b in boxes if b["score"] >= cut]
    return ok[0] if ok else None


def position_check(det_in, det_out, trackable, cut):
    """Compare detections of the input (det_in) and the composited file (det_out) for the trackable queries."""
    rows, ok = [], True
    for q in trackable:
        b_in = best_box(det_in.get(q, []), cut)
        if b_in is None:
            rows.append({"object": q, "in_input": False, "pass": True, "note": "not found in the input; not checked"})
            continue
        cands = [b for b in det_out.get(q, []) if b["score"] >= cut]
        best = max(cands, key=lambda b: K.iou(b_in["box"], b["box"]), default=None)
        iou = round(K.iou(b_in["box"], best["box"]), 3) if best else 0.0
        passed = iou >= IOU_MIN
        ok = ok and passed
        rows.append({"object": q, "in_input": True, "input_box": b_in["box"], "input_score": b_in["score"],
                     "output_box": best["box"] if best else None, "output_score": best["score"] if best else None,
                     "iou": iou, "pass": passed})
    return ok, rows


def cmd_fix():
    """Write the amendment and each scene's tracked and untrackable objects into thresholds.json (once)."""
    import json
    t = json.loads(C.THRESHOLDS.read_text(encoding="utf-8"))
    if "tracked_objects" in t:
        raise SystemExit("tracked_objects already written; they are fixed")
    cut = t["numbers"]["detector_score_cut"]["value"]
    det = K.Detector()
    S = C.read_set_a()
    out = {}
    for scene in C.MAIN_SCENES + ["SA-R1", "SA-R2"]:
        r = tracked_objects(S[scene])
        src = C.OUT / f"{scene}_source.png"
        found = det.detect(C.load_rgb(src), r["tracked"])
        scores = {q: (found[q][0]["score"] if found[q] else 0.0) for q in r["tracked"]}
        out[scene] = {"noun_chunk_heads": r["nouns"], "excluded": r["excluded"], "tracked": r["tracked"],
                      "trackable": [q for q in r["tracked"] if scores[q] >= cut],
                      "untrackable": [q for q in r["tracked"] if scores[q] < cut],
                      "best_score_in_accepted_source": scores, "source_file": src.name,
                      "source_sha256": C.sha256_file(src)}
        print(scene, "trackable", out[scene]["trackable"], "| untrackable", out[scene]["untrackable"], flush=True)
    t["tracked_objects"] = out
    t["amendments"].append({
        "utc": C.now(), "date": "29 October 2026",
        "what": "Object-position check replaces the spill check for every Set A addition",
        "decided_by": "David G. Kamper, 29 October 2026, before any participant data",
        "supersedes": "the spill check of 28 October 2026; its values stay in each candidate's previous_judgments and "
                      "in manifest.csv",
        "rule": ("Tracked objects (fixed per scene before any judging, in tracked_objects): the noun chunks (spaCy "
                 f"{spacy.__version__}, en_core_web_sm {nlp().meta['version']}) of the scene's Composition and "
                 "Background sentences in the bank; each chunk's head noun as the detector query 'a' or 'an' + noun; "
                 "excluded: the scene's added elements at all three amounts, the person or people of the Subject "
                 "sentence, and the surfaces and regions " + ", ".join(sorted(SURFACES)) + ". A tracked object is "
                 "trackable when the detector finds it in the accepted source at or above the score cut; otherwise "
                 "it is untrackable and ignored. A file passes when every trackable object found in its input (at or "
                 "above the cut) is also found in the composited file, at or above the cut, by a box whose "
                 f"intersection over union with the object's box in the input is at least {IOU_MIN} (a fixed constant, "
                 "not tuned); for each object the best-matching box is used. The input is the source for small and "
                 "medium, and the accepted medium for large."),
        "readings_made_determinate": (
            "Head noun: the chunk's root token when it is a noun, lemmatized to the singular ('oars' -> 'an oar'); "
            "chunks whose root is a pronoun ('She', 'his right') are skipped. 'an' before a vowel letter, else 'a'. "
            "Added elements: the head noun of each element phrase's first noun chunk and the noun (last word, and its "
            "singular) of the element's detector query, for the small, medium and large phrases in use. Person: the "
            "head noun of the Subject sentence's first noun chunk, in a scene with a person. The object's box in the "
            "input: its best-scoring box at or above the cut; an object not found in a file's input is not checked "
            "for that file. The lists are the rule's literal output and include chunk heads that are not objects "
            "('a hand', 'a band', 'a front', 'a glow'); they are applied as written."),
        "reason": ("The spill check measures pixel change: it penalized re-rendered texture (SA-R2's hay) and passed a "
                   "moved object of modest size (SA04's chair). A1's statement promises that no existing object moved "
                   "or vanished, which this check tests directly."),
        "consequences": ("Every addition in use is re-judged in candidate order under all current checks with the "
                         "object-position check in place of the spill check, starting with SA-R2 small's existing "
                         "candidates; when a medium changes, its large is searched again; searches continue under the "
                         "rescue rule."),
    })
    C.THRESHOLDS.write_text(json.dumps(t, indent=2, ensure_ascii=False), encoding="utf-8")


def check_file(det, rec_file, input_file, kind_scene, trackable, cut):
    out = det.detect(C.load_rgb(rec_file), trackable)
    inp = det.detect(C.load_rgb(input_file), trackable)
    return position_check(inp, out, trackable, cut)


if __name__ == "__main__":
    import sys
    {"fix": cmd_fix}[sys.argv[1]]()

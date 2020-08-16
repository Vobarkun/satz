import json
from enum import IntEnum
import random
from dataclasses import dataclass
import difflib

class Dictable:
    @classmethod
    def dict(cls, *args):
        if len(args) == 1:
            args = args[0]
        if len(args) != len(cls):
            raise TypeError("wrong number of values")
        return {key: args[key] for key in cls}

class casus(Dictable, IntEnum):
    nominativ = 0
    genitiv = 1
    dativ = 2
    akkusativ = 3
class numerus(Dictable, IntEnum):
    singular = 0
    plural = 1
class person(Dictable, IntEnum):
    erste = 0
    zweite = 1
    dritte = 2
class tempus(Dictable, IntEnum):
    präsens = 0
    präteritum = 1
    perfekt = 2
    plusquamperfekt = 3
    futur1 = 4
    futur2 = 5
class genus(Dictable, IntEnum):
    maskulin = 0
    feminin = 1
    neutrum = 2
class determination(Dictable, IntEnum):
    definit = 0
    indefinit = 1
class modus(Dictable, IntEnum):
    indikativ = 0
    konjunktiv1 = 1
    konjunktiv2 = 2
    imperativ = 3
class genusverbi(Dictable, IntEnum):
    aktiv = 0
    passiv = 1
class satz(Dictable, IntEnum):
    hauptsatz = 0
    nebensatz = 1
class hilfsverb(Dictable, IntEnum):
    haben = 0
    sein = 1
class komparation(Dictable, IntEnum):
    positiv = 0
    komparativ = 1
    superlativ = 2

@dataclass
class FP:
    casus: casus = None
    numerus: numerus = None
    person: person = None
    tempus: tempus = None
    genus: genus = None
    determination: determination = None
    modus: modus = None
    genusverbi: genusverbi = None
    satz: satz = None
    komparation: komparation = None

    def __iter__(self):
        for value in vars(self).values():
            if value is not None:
                yield value


with open("data/substantive.json", encoding = "utf8") as f:
    substantive = json.loads(f.read())
with open("data/adjektive.json", encoding = "utf8") as f:
    adjektive = json.loads(f.read())
with open("data/verben.json", encoding = "utf8") as f:
    verben = json.loads(f.read())

with open("data/verbenmitobjekt.json", encoding = "utf8") as f:
    verbenmitobjekt = json.loads(f.read())
with open("data/vornamen.txt", encoding = "utf8") as f:
    vornamen = f.read().splitlines()
with open("data/numerale.txt", encoding = "utf8") as f:
    numerale = f.read().splitlines()

lsubstantive = list(substantive)
lverben = list(verben)
ladjektive = list(adjektive)
lfeminin = [w for w in lsubstantive if substantive[w]["genus"] == "feminin"]
lmaskulin = [w for w in lsubstantive if substantive[w]["genus"] == "maskulin"]
lneutrum = [w for w in lsubstantive if substantive[w]["genus"] == "neutrum"]
dictverbenmitobjekt = {v[0]:v for v in verbenmitobjekt}

def retrieve(d, *args):
    keys = {}
    for arg in args:
        if not type(arg) is str:
            try:
                for key in arg:
                    keys[type(key)] = key
                continue
            except TypeError:
                pass
        keys[type(arg)] = arg
    while type(d) is dict:
        d = d[keys[type(list(d)[0])]]
    return d

def flektiereSubstantiv(word, fp):
    data = substantive[word]
    artikel = {
        numerus.singular: {
            determination.definit: {
                genus.maskulin: casus.dict("der", "des", "dem", "den"),
                genus.feminin: casus.dict("die", "der", "der", "die"),
                genus.neutrum: casus.dict("das", "des", "dem", "das")
            },
            determination.indefinit: {
                genus.maskulin: casus.dict("ein", "eines", "einem", "einen"),
                genus.feminin: casus.dict("eine", "einer", "einer", "eine"),
                genus.neutrum: casus.dict("ein", "eines", "einem", "ein")
            }
        },
        numerus.plural: determination.dict(casus.dict("die", "der", "den", "die"), "")
    }
    selbst = numerus.dict([casus.dict([data["flexion"][c.name][n] for c in casus]) for n in numerus])
    g = {"maskulin": genus.maskulin, "feminin": genus.feminin, "neutrum": genus.neutrum}[data["genus"]]
    return (retrieve(artikel, fp, g) + " " + retrieve(selbst, fp, g)).strip().replace("  ", " ")

def flektiereAdjektiv(word, fp):
    data = adjektive[word]
    endung = {
        numerus.singular: genus.dict(casus.dict(determination.dict("e", "er"), "en", "en", "en"), casus.dict("e", "en", "en", "e"), casus.dict(determination.dict("e", "es"), "en", "en", determination.dict("e", "es"))),
        numerus.plural: determination.dict("en", casus.dict("e", "er", "en", "e"))
    }
    stamm = {komparation.positiv: data["positiv"].rstrip("e"), komparation.komparativ: data["komparativ"], komparation.superlativ: data["superlativ"].rstrip("n").rstrip("e")}
    return (retrieve(stamm, fp) + retrieve(endung, fp)).strip().replace("  ", " ")

def flektiereVerb(infinitiv, fp):
    data = verben[infinitiv]
    def join(stamm, endung):
        if endung != "":
            if (stamm[-1] == "s" and endung[0] == "s") or (infinitiv[-2:] in ["ln", "rn"] and endung[0] == "e"):
                endung = endung[1:]
            elif (stamm[-1] == "ß" and endung[0] == "s") or (stamm[-1] != "e" and endung[0] == "n") or (stamm[-1] in "dt" and endung[0] in "st"):
                endung = "e" + endung
        return stamm + endung
    präfix = (data["flexion"]["präsens"][0].split(" ") + [""])[1]
    stamm = infinitiv.rstrip("n").rstrip("e")[len(präfix):]
    partizip2 =  data["flexion"]["partizip2"]
    präteritum = data["flexion"]["präteritum"].split(" ")[0]
    konjunktiv2 = data["flexion"]["konjunktiv2"].split(" ")[0].rstrip("e")
    mitte = {
        genusverbi.aktiv: {
            tempus.präsens: {
                modus.indikativ: {
                    numerus.singular: {
                        satz.hauptsatz: person.dict([data["flexion"]["präsens"][p].split(" ")[0] for p in person]),
                        satz.nebensatz: person.dict([präfix + data["flexion"]["präsens"][p].split(" ")[0] for p in person])
                    },
                    numerus.plural: {
                        satz.hauptsatz: person.dict([join(stamm, e) for e in  ["en", "t", "en"]]),
                        satz.nebensatz: person.dict([präfix + join(stamm, e) for e in  ["en", "t", "en"]])
                    }
                },
                modus.imperativ: data["flexion"]["imperativ"][fp.numerus].split(" ")[0],
                modus.konjunktiv1: {
                    numerus.singular: person.dict([satz.dict(stamm + e, präfix + stamm + e) for e in ["e", "est", "e"]]),
                    numerus.plural: person.dict([satz.dict(präfix + stamm + e, präfix + stamm + e) for e in ["en", "et", "en"]])
                }
            },
            tempus.präteritum: {
                modus.indikativ: {
                    satz.hauptsatz: numerus.dict(person.dict([join(präteritum, e) for e in ["", "st", ""]]), person.dict([join(präteritum, e) for e in ["n", "t", "n"]])),
                    satz.nebensatz: numerus.dict(person.dict([präfix + join(präteritum, e) for e in ["", "st", ""]]), person.dict([präfix + join(präteritum, e) for e in ["n", "t", "n"]]))
                },
                modus.konjunktiv2: {
                    satz.hauptsatz: numerus.dict(person.dict([konjunktiv2 + e for e in ["e", "est", "e"]]), person.dict([konjunktiv2 + e for e in ["en", "et", "en"]])),
                    satz.nebensatz: numerus.dict(person.dict([präfix + konjunktiv2 + e for e in ["e", "est", "e"]]), person.dict([konjunktiv2 + e for e in ["en", "et", "en"]]))
                }
            },
            tempus.perfekt: partizip2, tempus.plusquamperfekt: partizip2, tempus.futur1: infinitiv, tempus.futur2: partizip2
        },
        genusverbi.passiv: partizip2
    }
    links = {
        genusverbi.aktiv: {
            modus.indikativ: {
                tempus.präsens: "",
                tempus.präteritum: "",
                tempus.perfekt: {
                    hilfsverb.haben: numerus.dict(person.dict("habe", "hast", "hat"), person.dict("haben", "habt", "haben")),
                    hilfsverb.sein: numerus.dict(person.dict("bin", "bist", "ist"), person.dict("sind", "seid", "sind"))
                },
                tempus.plusquamperfekt: {
                    hilfsverb.haben: numerus.dict(person.dict("hatte", "hattest", "hatte"), person.dict("hatten", "hattet", "hatten")),
                    hilfsverb.sein: numerus.dict(person.dict("war", "warst", "war"), person.dict("waren", "wart", "waren"))
                },
                **dict.fromkeys([tempus.futur1, tempus.futur2], numerus.dict(person.dict("werde", "wirst", "wird"), person.dict("werden", "werdet", "werden")))
            },
            modus.imperativ: {
                tempus.präsens: "",
                tempus.perfekt: hilfsverb.dict(numerus.dict("habe", "habt"), numerus.dict("sei", "seid")),
            },
            modus.konjunktiv1: {
                tempus.präsens: "",
                tempus.perfekt: {
                    hilfsverb.haben: numerus.dict(person.dict("habe", "habest", "habe"), person.dict("haben", "habet", "haben")),
                    hilfsverb.sein: numerus.dict(person.dict("sei", "seist", "sei"), person.dict("seien", "seiet", "seien"))
                },
                **dict.fromkeys([tempus.futur1, tempus.futur2], numerus.dict(person.dict("werde", "werdest", "werde"), person.dict("werden", "werdet", "werden")))
            },
            modus.konjunktiv2: {
                tempus.präteritum: "",
                tempus.plusquamperfekt: {
                    hilfsverb.haben: numerus.dict(person.dict("hätte", "hättest", "hätte"), person.dict("hätten", "hättet", "hätten")),
                    hilfsverb.sein: numerus.dict(person.dict("wäre", "wärest", "wäre"), person.dict("wären", "wärt", "wären"))
                },
                **dict.fromkeys([tempus.futur1, tempus.futur2], numerus.dict(person.dict("würde", "würdest", "würde"), person.dict("würden", "würdet", "würden")))
            }
        },
        genusverbi.passiv: {
            modus.indikativ: {
                tempus.präteritum: numerus.dict(person.dict("wurde", "wurdest", "wurde"), person.dict("wurden", "wurdet", "wurden")),
                tempus.perfekt: numerus.dict(person.dict("bin", "bist", "ist"), person.dict("sind", "seid", "sind")),
                tempus.plusquamperfekt: numerus.dict(person.dict("war", "warst", "war"), person.dict("waren", "wart", "waren")),
                **dict.fromkeys([tempus.präsens, tempus.futur1, tempus.futur2], numerus.dict(person.dict("werde", "wirst", "wird"), person.dict("werden", "werdet", "werden")))
            },
            modus.imperativ: {
                tempus.präsens: numerus.dict("werde", "werdet"),
                tempus.perfekt: numerus.dict("sei", "seid")
            },
            modus.konjunktiv1: {
                tempus.perfekt: numerus.dict(person.dict("sei", "seist", "sei"), person.dict("seien", "seiet", "seien")),
                **dict.fromkeys([tempus.präsens, tempus.futur1, tempus.futur2], numerus.dict(person.dict("werde", "werdest", "werde"), person.dict("werden", "werdet", "werden")))
            },
            modus.konjunktiv2: {
                tempus.plusquamperfekt: numerus.dict(person.dict("wäre", "wärest", "wäre"), person.dict("wären", "wäret", "wären")),
                **dict.fromkeys([tempus.präteritum, tempus.futur1, tempus.futur2], numerus.dict(person.dict("würde", "würdest", "würde"), person.dict("würden", "würdet", "würden")))
            }
        }
    }
    rechts = {
        genusverbi.aktiv: {
            tempus.präsens: satz.dict(präfix, ""),
            tempus.präteritum: satz.dict(präfix, ""),
            tempus.perfekt: "", tempus.plusquamperfekt: "",
            tempus.futur1: "", tempus.futur2: hilfsverb.dict("haben", "sein")
        },
        genusverbi.passiv: {
            tempus.präsens: "", tempus.präteritum: "",
            tempus.perfekt: "worden", tempus.plusquamperfekt: "worden",
            tempus.futur1: "werden", tempus.futur2: "worden sein"
        }
    }
    hv = hilfsverb("sein" in data["hilfsverb"])
    if fp.satz == satz.hauptsatz:
        return (retrieve(links, fp, hv) + " " + retrieve(mitte, fp) + " " + retrieve(rechts, fp, hv)).strip().replace("  ", " ")
    else:
        return (retrieve(mitte, fp) + " " + retrieve(rechts, fp, hv) + " " + retrieve(links, fp, hv)).strip().replace("  ", " ")

def reflexivpronomen(fp):
    d = {
        numerus.singular: person.dict("mich", "dich", "sich"),
        numerus.plural: person.dict("uns", "euch", "sich")
    }
    return retrieve(d, fp)

nextWord = {"feminin": [], "maskulin": [], "neutrum": [], "verb": [], "adjektiv": [], "vorname": [], "verbmitobjekt": []}

def clearNext():
    for k in nextWord:
        nextWord[k] = []

def setNext(word):
    for s in [word, word.lower(), word.capitalize()]:
        for t, l in [("verbmitobjekt", dictverbenmitobjekt), ("vorname", vornamen), ("feminin", lfeminin), ("maskulin", lmaskulin), ("neutrum", lneutrum), ("verb", verben), ("adjektiv", adjektive)]:
            if s in l:
                nextWord[t].append(s)
                return True

    return False

def randomVerbmitObjekt():
    word = random.choice(verbenmitobjekt)
    if nextWord["verbmitobjekt"]:
        word = dictverbenmitobjekt[nextWord["verbmitobjekt"].pop(0)]
    return word

def randomVorname():
    word = random.choice(vornamen)
    if nextWord["vorname"]:
        word = nextWord["vorname"].pop(0)
    return word

def randomNumeral():
    return random.choice(numerale)

def randomSubstantiv(fp):
    while True:
        word = random.choice(list(substantive))
        if fp.genus is not None:
            if nextWord[fp.genus.name]:
                word = nextWord[fp.genus.name].pop(0)
        if substantive[word]["genus"] != fp.genus.name:
            continue
        form = flektiereSubstantiv(word, fp)
        if not "-" in form:
            return form

def randomVerb():
    while True:
        word = random.choice(list(verben))
        if nextWord["verb"]:
            word = nextWord["verb"].pop(0)
        return word

def randomAdjektiv(fp):
    while True:
        word = random.choice(list(adjektive))
        if nextWord["adjektiv"]:
            word = nextWord["adjektiv"].pop(0)
        form = flektiereAdjektiv(word, fp)
        if not "-" in form:
            return form



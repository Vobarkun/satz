import grammatik as gr
import random
import copy
import json
import re
import sys
from googletrans import Translator
translator = Translator()

def rchoice(enum, weights = None):
    if weights is None:
        weights = [1 for e in enum]
    return random.choice([e for e, w in zip(enum, weights) for _ in range(w)])

class Node:
    def __init__(self, fp):
        self.fp = copy.copy(fp)

    def evaluate(self):
        pass

class Satz(Node):
    def __init__(self, fp = None):
        super().__init__(fp)
        if self.fp is None:
           self.fp = gr.FP(satz = gr.satz.hauptsatz)
        if self.fp.numerus is None:
            self.fp.numerus = rchoice(gr.numerus)
        if self.fp.person is None:
            self.fp.person = rchoice(gr.person, [1, 1, 10])

    def evaluate(self):
        subjekt = Subjekt(self.fp)
        prädikat = Prädikat(self.fp)
        self.text = subjekt.evaluate() + " " + prädikat.evaluate()
        if self.fp.satz == gr.satz.hauptsatz and (len(self.text) < 50 and random.random() < 0.5) and prädikat.fp.tempus not in [gr.tempus.futur1, gr.tempus.futur2]:
            gleichzeitig = ["weil", "obwohl", "da", "bevor", "als", "bis", "ehe", "während", "falls", "indem", "obgleich", "obschon", "obzwar", "ohne dass", "sobald", "sodass", "wenn", "wohingegen"]
            vorzeitig = ["nachdem", "als", "sobald", "seitdem", "sowie", "seit"]
            vorzeit = {gr.tempus.präsens: gr.tempus.perfekt, gr.tempus.präteritum: gr.tempus.plusquamperfekt, gr.tempus.futur1: gr.tempus.futur2}
            g = True if prädikat.fp.tempus in [gr.tempus.perfekt, gr.tempus.plusquamperfekt, gr.tempus.futur2] else random.random() < 0.5
            subjunktion = random.choice(gleichzeitig if g else vorzeitig)
            nebensatz = Satz(gr.FP(satz = gr.satz.nebensatz, tempus = prädikat.fp.tempus if g else vorzeit[prädikat.fp.tempus]))
            self.text += ", " + subjunktion + " " + nebensatz.evaluate()
        return self.text

class Prädikat(Node):
    def __init__(self, fp):
        super().__init__(fp)
        if self.fp.modus is None:
            self.fp.modus = gr.modus.indikativ
        if self.fp.tempus is None:
            if self.fp.modus == gr.modus.indikativ:
                self.fp.tempus = rchoice(gr.tempus, [10, 10, 10, 1, 5, 1])
            elif self.fp.modus == gr.modus.konjunktiv1:
                self.fp.tempus = rchoice([gr.tempus.präsens, gr.tempus.perfekt, gr.tempus.futur1, gr.tempus.futur2], [10, 5, 5, 5])
            elif self.fp.modus == gr.modus.konjunktiv1:
                self.fp.tempus = rchoice([gr.tempus.präteritum, gr.tempus.plusquamperfekt, gr.tempus.futur1, gr.tempus.futur2], [10, 5, 5, 5])
        if self.fp.genusverbi is None:
            self.fp.genusverbi = gr.genusverbi.aktiv

    def evaluate(self):
        if random.random() < 0.8:
            verbmo = gr.randomVerbmitObjekt()
        else:
            verbmo = [gr.randomVerb()]
        self.text = gr.flektiereVerb(verbmo[0], self.fp)

        if "akkusativ" in verbmo[1:] and random.random() < 0.1:
            verbmo.remove("akkusativ")
            verbmo.insert(1, "sich")

        if random.random() < 0.4:
            i = 1
            if "sich" in verbmo:
                i = verbmo.index("sich") + 1
            verbmo.insert(i, "adverb")

        objekttext = " "
        for obj in verbmo[1:]:
            if "akkusativ" == obj:
                objekt = Objekt(gr.FP(casus = gr.casus.akkusativ))
                objekttext += " " + objekt.evaluate() + " "
            elif "dativ" == obj:
                objekt = Objekt(gr.FP(casus = gr.casus.dativ))
                objekttext += " " + objekt.evaluate() + " "
            elif "akkusativ" in obj:
                objekt = Objekt(gr.FP(casus = gr.casus.akkusativ))
                objekttext += " " + obj.split(" ")[0] + " " + objekt.evaluate() + " "
            elif "dativ" in obj:
                objekt = Objekt(gr.FP(casus = gr.casus.dativ))
                objekttext += " " + obj.split(" ")[0] + " " + objekt.evaluate() + " "
            elif "zu infinitiv" == obj:
                infinitiv = random.choice(list(gr.verben)).capitalize()
                objekttext += " zum " + infinitiv + " "
            elif "sich" == obj:
                objekttext += " " + gr.reflexivpronomen(self.fp) + " "
            elif "adverb" == obj:
                adverbial = Adverbial(self.fp)
                objekttext += " " + adverbial.evaluate() + " "
        

        if self.fp.satz == gr.satz.hauptsatz:
            if not " " in self.text:
                self.text = self.text + " "
            self.text = self.text.replace(" ", objekttext, 1)
        elif self.fp.satz == gr.satz.nebensatz:
            self.text = objekttext + self.text

        if "dass indikativ" in verbmo[1:]:
            nebensatz = Satz(gr.FP(satz = gr.satz.nebensatz, modus = gr.modus.indikativ))
            self.text += ", dass " + nebensatz.evaluate() + " "
        if "dass konjunktiv" in verbmo[1:]:
            nebensatz = Satz(gr.FP(satz = gr.satz.nebensatz, modus = gr.modus.konjunktiv1))
            self.text += ", dass " + nebensatz.evaluate() + " "

        return self.text

class Subjekt(Node):
    def __init__(self, fp):
        super().__init__(fp)
        if self.fp.genus is None:
            self.fp.genus = rchoice(gr.genus)
        if self.fp.determination is None:
            self.fp.determination = rchoice(gr.determination)
        self.fp.casus = gr.casus.nominativ

    def evaluate(self):
        if self.fp.person != gr.person.dritte:
            self.text = gr.retrieve({gr.person.erste: gr.numerus.dict("ich", "wir"), gr.person.zweite: gr.numerus.dict("du", "ihr")}, self.fp)
        else:
            if random.random() < 0.9 or self.fp.numerus == gr.numerus.plural:
                self.substantiv = Substantiv(self.fp)
                self.text = self.substantiv.evaluate()
            else:
                self.text = gr.randomVorname()
        return self.text

class Objekt(Node):
    def __init__(self, fp):
        super().__init__(fp)
        if self.fp.casus is None:
            self.fp.casus = random.choice([gr.casus.dativ, gr.casus.akkusativ])

    def evaluate(self):
        if random.random() < 0.9:
            self.substantiv = Substantiv(self.fp)
            self.text = self.substantiv.evaluate()
        else:
            self.text = gr.randomVorname()
        return self.text

class Substantiv(Node):
    def __init__(self, fp):
        super().__init__(fp)
        if self.fp.genus is None:
            self.fp.genus = rchoice(gr.genus)
        if self.fp.determination is None:
            self.fp.determination = rchoice(gr.determination)
        if self.fp.casus is None:
            self.fp.casus = rchoice(gr.casus)
        if self.fp.numerus is None:
            self.fp.numerus = rchoice(gr.numerus)
        if self.fp.casus == gr.casus.genitiv and self.fp.numerus == gr.numerus.plural:
            self.fp.determination = gr.determination.definit

    def evaluate(self):
        self.text = gr.randomSubstantiv(self.fp)
        if not " " in self.text:
                self.text = " " + self.text
        if random.random() < 0.5:
            self.adjektiv = Adjektiv(self.fp)
            self.text = self.text.replace(" ", " " + self.adjektiv.evaluate() + " ", 1)
        if self.fp.numerus == gr.numerus.plural and random.random() < 0.2:
            self.text = self.text.replace(" ", " " + gr.randomNumeral() + " ", 1)
        if random.random() < 0.1 and self.fp.casus != gr.casus.genitiv:
            genitiv = Substantiv(gr.FP(casus = gr.casus.genitiv))
            self.text += " " + genitiv.evaluate() + " "
        return self.text

class Adjektiv(Node):
    def __init__(self, fp):
        super().__init__(fp)
        if self.fp.komparation is None:
            self.fp.komparation = rchoice(gr.komparation, [50, 1, 1])

    def evaluate(self):
        if random.random() < 0.5 and self.fp.komparation == gr.komparation.positiv:
            self.text = gr.flektiereAdjektiv(gr.flektiereVerb(gr.randomVerb(), random.choice(["partizip1", "partizip2"])), self.fp)
        else:
            self.text = gr.randomAdjektiv(self.fp)
        return self.text

class Adverbial(Node):
    def __init__(self, fp = gr.FP()):
        super().__init__(fp)
        
    def evaluate(self):
        if random.random() < 0.9:
            self.text = gr.randomAdverb()
        else:
            adjektiv = Adjektiv(gr.FP(stamm=True))
            self.text = adjektiv.evaluate()
        return self.text

def satz(theme = []):
    if type(theme) is str:
        theme = theme.split(",")
    
    dest = False
    for t in theme:
        if len(t) <= 2:
            dest = t
            break
    if dest:
        theme.remove(dest)

    l = 100000
    satz = "error"
    for i in range(1000):
        gr.clearNext()
        for t in theme:
            gr.setNext(t)
        s = Satz().evaluate()
        nl = sum([len(e) for e in list(gr.nextWord.values())])
        if nl < l:
            satz = s
            l = nl
        if l == 0:
            break
    satz = re.sub(" +", " ", satz).strip()
    satz = re.sub(" +,", ",", satz)
    satz = re.sub(",+", ",", satz)
    satz = satz[0].upper() + satz[1:] + "."
    if dest:
        try:
            satz = translator.translate(satz, dest=dest).text
        except Exception:
            pass
    return satz

if __name__ == "__main__":
    for i in range(5):
        print(satz(sys.argv[1] if len(sys.argv) > 1 else ""))
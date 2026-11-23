#!/usr/bin/env python3
"""
Lewy Body Gene Therapy Vector Designer
======================================

A desktop design tool for CNS gene therapy vectors aimed at alpha-synuclein
and Lewy pathology in neurons.  Pick a strategy and target, assemble the
expression cassette, check AAV/lentiviral packaging limits, and export a
GenBank or FASTA file.

Standard library only: needs Python 3.9+ with tkinter.
    Windows / macOS : tkinter ships with python.org installers.
    Debian / Ubuntu : sudo apt install python3-tk
    Fedora          : sudo dnf install python3-tkinter

Run with:
    python3 lewy_vector_designer.py

Research design tool.  Producing virus requires institutional biosafety
approval, and clinical gene therapy products need GMP manufacturing,
preclinical safety and efficacy data, and regulatory authorization.
"""

from __future__ import annotations

import datetime
import re

APP_TITLE = "Lewy Body Gene Therapy Vector Designer"
APP_SUB = ("Design CNS vectors aimed at α-synuclein and Lewy pathology: pick a strategy "
           "and target, assemble the cassette, check packaging limits, export GenBank.")

# --------------------------------------------------------------------------
# Element libraries.  Lengths are typical values in base pairs; elements
# without a built-in sequence export as N until a verified sequence is pasted.
# --------------------------------------------------------------------------

PROM = {"hSyn1": 469, "CaMKIIa": 1292, "TH (2.5 kb)": 2500, "GfaABC1D": 681,
        "CAG": 1733, "CBh": 800, "CMV": 508, "EF1a": 1178, "EFS": 212,
        "PGK": 516, "UbC": 1220}
POL3 = {"U6": 241, "H1": 231, "7SK": 244}
MARK = {"none": 0, "EGFP": 720, "mCherry": 711, "Puro": 600, "Neo": 795, "Blast": 399}
POLYA = {"bGH": 225, "SV40": 122, "none": 0}
RESIST = {"AmpR": 861, "KanR": 816}
LINK = {"P2A": 0, "IRES": 580, "separate PGK promoter": 516}
LOCAL = {"intracellular (cytosol)": 0, "secreted (IgK leader)": 60, "ER-retained (KDEL)": 12}
DEGRON = {"none": 0, "PEST (ODC)": 120, "CL1": 48, "NSlmb F-box": 450}
TAGS = {
    "none": "",
    "FLAG3": "GACTACAAAGACCATGACGGTGATTATAAAGATCATGACATCGACTACAAGGATGACGATGACAAG",
    "HA": "TACCCATACGATGTTCCAGATTACGCT",
    "Myc": "GAACAAAAACTCATCTCAGAAGAGGATCTG",
    "His6": "CATCACCATCACCATCAC",
}

P2A_SEQ = "GGAAGCGGAGCTACTAACTTCAGCCTGCTGAAGCAGGCTGGAGACGTGGAGGAGAACCCTGGACCT"
SGRNA_SCAFFOLD = ("GTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGTGGCACC"
                  "GAGTCGGTGC")
KDEL_SEQ = "AAGGACGAGCTG"
GS_LINKER = "GGCGGAGGCGGATCT"
MIR_5P, MIR_LOOP, MIR_3P = "TGCTGTTGACAGTGAGCG", "TAGTGAAGCCACAGATGTA", "TGCCTACTGCCTCGGA"

SEROTYPES = {
    "AAV9": "Broad CNS spread and some blood-brain barrier crossing at high systemic dose. "
            "The usual starting point for widespread neuronal targeting.",
    "AAV2": "Classic CNS serotype with strong neuronal tropism but limited spread from the "
            "injection site. Well suited to focal putaminal or nigral delivery.",
    "AAV5": "Wide parenchymal spread in striatum and cortex; transduces astrocytes as well "
            "as neurons, so pair it with a neuron-specific promoter.",
    "AAV1": "Strong neuronal transduction with anterograde transport along projections.",
    "AAV6": "Good neuronal transduction with retrograde transport; often used for "
            "circuit-level targeting.",
    "AAVrh10": "Broad and efficient CNS spread, including after intrathecal delivery.",
    "AAV-DJ": "Engineered hybrid with broad tropism; mostly used in culture and early "
              "in vivo work.",
    "AAV-PHP.eB": "Engineered for efficient brain-wide transduction after intravenous "
                  "dosing, but this depends on the mouse Ly6a receptor and does not "
                  "transfer to primates or patients.",
}

ROUTES = {
    "intraparenchymal (putamen)":
        "Convection-enhanced delivery into putamen gives high local dose with minimal "
        "systemic exposure. Coverage of substantia nigra depends on retrograde transport "
        "by the capsid.",
    "intraparenchymal (substantia nigra)":
        "Direct nigral delivery reaches dopaminergic cell bodies but transduces a small "
        "volume; it is a surgically demanding target.",
    "intrathecal / intracisternal":
        "Reaches spinal cord, brainstem and superficial cortex with lower vector dose than "
        "intravenous delivery; deep grey structures are transduced less well.",
    "intracerebroventricular":
        "Broad ependymal and periventricular transduction; parenchymal penetration falls "
        "off with distance from the ventricle.",
    "intravenous (systemic)":
        "Requires a barrier-crossing capsid and a high dose, with substantial liver "
        "exposure. Consider liver detargeting and a neuron-specific promoter.",
}

# gene -> (typical ORF length in bp, biology note)
GENES = {
    "Custom": (1000, ""),
    "SNCA": (423,
             "Encodes α-synuclein, the main component of Lewy bodies. α-synuclein "
             "has normal presynaptic functions, so aim for partial knockdown: near-complete "
             "nigral knockdown has caused dopaminergic toxicity in rodents and non-human "
             "primates."),
    "SNCB": (405,
             "β-synuclein, which inhibits α-synuclein aggregation. Usually a "
             "comparator rather than a knockdown target."),
    "LRRK2": (7584,
              "Kinase whose activity is raised in both familial and sporadic disease. The ORF "
              "is far too large for AAV and awkward for lentivirus, so LRRK2 is normally "
              "addressed by knockdown or small molecules rather than gene replacement."),
    "GBA1": (1611,
             "Glucocerebrosidase. GBA1 variants are the commonest genetic risk factor for "
             "Lewy body disease, and raising lysosomal GCase activity lowers α-synuclein "
             "in models."),
    "TFEB": (1428,
             "Master transcription factor for autophagy and lysosome biogenesis. Constitutive "
             "overexpression broadly reprograms the lysosomal system, so consider a regulated "
             "or modest promoter."),
    "LAMP2A": (1233,
               "Receptor for chaperone-mediated autophagy, which degrades α-synuclein "
               "directly. LAMP2A declines with age and in affected nigra."),
    "SCARB2": (1437,
               "LIMP-2, the trafficking receptor that delivers GCase to the lysosome. An "
               "alternative to delivering GBA1 itself."),
    "PRKN": (1398,
             "Parkin, an E3 ubiquitin ligase acting in mitophagy and protein quality control."),
    "BECN1": (1353, "Beclin-1, which initiates autophagosome formation."),
    "VPS35": (2370,
              "Retromer subunit governing endosomal sorting; the D620N variant causes dominant "
              "parkinsonism."),
    "NFE2L2": (1818,
               "NRF2, the antioxidant and proteostasis transcription factor. Sustained "
               "constitutive activation carries a theoretical oncogenic risk; prefer regulated "
               "expression."),
    "HSPA8": (1941,
              "HSC70, the chaperone that delivers substrates to chaperone-mediated autophagy."),
    "DNAJB6": (981,
               "J-domain co-chaperone that suppresses amyloid nucleation at substoichiometric "
               "levels; isoform b is the potent anti-aggregation form."),
    "BAG3": (1725,
             "Co-chaperone that routes aggregation-prone clients to autophagy."),
    "STUB1": (912,
              "CHIP, a chaperone-dependent E3 ligase that ubiquitinates α-synuclein for "
              "degradation."),
    "HSPB1": (618,
              "Hsp27, a small heat-shock protein that binds early α-synuclein oligomers."),
    "PLK2": (2058,
             "Kinase that phosphorylates α-synuclein at Ser129 and promotes its autophagic "
             "clearance. Note that Ser129 phosphorylation is itself a Lewy body marker, so "
             "interpret readouts carefully."),
    "NbSyn87": (366,
                "Single-domain nanobody against the α-synuclein C-terminus. Small enough "
                "to fit comfortably in scAAV."),
    "NbSyn2": (366,
               "Single-domain nanobody against the α-synuclein C-terminus with a distinct "
               "epitope."),
    "VH14 intrabody": (366,
                       "Single-domain intrabody directed at the central hydrophobic NAC region "
                       "that drives aggregation."),
    "scFv-6E": (750,
                "Conformation-selective single-chain antibody that prefers oligomeric and "
                "fibrillar α-synuclein over the monomer."),
    "D5 scFv": (750, "Single-chain antibody selective for oligomeric α-synuclein."),
    "Custom binder": (400, ""),
    "GDNF": (636,
             "Glial cell line-derived neurotrophic factor. Neurotrophic support does not clear "
             "existing aggregates, and clinical trials of focal GDNF delivery have not met "
             "primary endpoints."),
    "NRTN": (591,
             "Neurturin, a GDNF-family ligand delivered as AAV2-neurturin in previous trials."),
    "CDNF": (702,
             "Cerebral dopamine neurotrophic factor, which also has ER-resident chaperone-like "
             "activity."),
    "BDNF": (744,
             "Brain-derived neurotrophic factor; broad expression carries off-target risks such "
             "as pain and weight loss."),
    "DDC": (1443,
            "AADC, the dopamine-synthesizing enzyme. A symptomatic strategy that improves "
            "levodopa conversion and does nothing to Lewy pathology."),
}

# strategy key -> (display name, target list, default promoter, default marker, tip)
STRATEGIES = {
    "knock": ("α-synuclein lowering (RNAi or CRISPR)",
              ["SNCA", "LRRK2", "Custom"], "hSyn1", "none",
              "Reduces synthesis of the aggregating protein. Partial, titratable knockdown is "
              "the goal; validated designs usually keep 40 to 60 percent of normal "
              "α-synuclein in nigral neurons."),
    "intra": ("Intrabody or nanobody against α-synuclein",
              ["NbSyn87", "NbSyn2", "VH14 intrabody", "scFv-6E", "D5 scFv", "Custom binder"],
              "hSyn1", "none",
              "Expresses a binder inside or around neurons to block aggregation or seeding. A "
              "degradation tag turns the binder into a targeted degrader; secretion instead "
              "intercepts extracellular, cell-to-cell seeding species."),
    "lyso": ("Lysosomal and autophagic clearance",
             ["GBA1", "SCARB2", "TFEB", "LAMP2A", "PRKN", "BECN1", "VPS35", "Custom"],
             "hSyn1", "none",
             "Raises degradative capacity so neurons clear α-synuclein faster. GBA1 and "
             "SCARB2 are the most clinically advanced routes."),
    "chap": ("Chaperone and proteostasis support",
             ["DNAJB6", "HSPA8", "BAG3", "STUB1", "HSPB1", "NFE2L2", "PLK2", "Custom"],
             "hSyn1", "none",
             "Supplies chaperone capacity that suppresses nucleation and holds "
             "α-synuclein in a degradable state."),
    "tropic": ("Neurotrophic and symptomatic support",
               ["GDNF", "NRTN", "CDNF", "BDNF", "DDC", "Custom"], "hSyn1", "none",
               "Supports surviving neurons or restores dopamine synthesis. These are "
               "adjunctive: they do not target Lewy pathology itself."),
    "model": ("α-synucleinopathy modeling (research use)",
              ["SNCA", "SNCB", "Custom"], "TH (2.5 kb)", "EGFP",
              "Human α-synuclein overexpression in nigra or cortex to build a model. Use "
              "the variant label for A53T, A30P, E46K or S129A. This is not a therapeutic "
              "design."),
}

SILENCING = ["shRNA", "shRNAmir (miR-E)", "sgRNA (knockout)", "sgRNA (CRISPRi)"]
REGIONS = ["coding sequence", "3′ UTR", "promoter / TSS"]

COLORS = {"guide": "#e56b2f", "ltr": "#6b7f90", "itr": "#6b7f90", "pack": "#9b7bd8",
          "promoter": "#e8a317", "cds": "#1fa971", "tag": "#18a5b8", "marker": "#e0483f",
          "reg": "#7a63d1", "polya": "#8497a5", "ori": "#a7b5c0", "bact": "#d6479a",
          "link": "#3b82d6", "stop": "#c0392b"}
GB_KEYS = {"ltr": "LTR", "itr": "repeat_region", "pack": "misc_feature",
           "promoter": "promoter", "cds": "CDS", "tag": "misc_feature", "marker": "CDS",
           "reg": "misc_feature", "polya": "polyA_signal", "ori": "rep_origin",
           "bact": "CDS", "link": "misc_feature", "stop": "misc_feature",
           "guide": "misc_feature"}

ENZYMES = {"EcoRI": "GAATTC", "BamHI": "GGATCC", "HindIII": "AAGCTT", "XhoI": "CTCGAG",
           "NotI": "GCGGCCGC", "NheI": "GCTAGC", "AgeI": "ACCGGT", "XbaI": "TCTAGA",
           "KpnI": "GGTACC", "MluI": "ACGCGT", "SalI": "GTCGAC", "PacI": "TTAATTAA"}

BUILT_IN = {"kozak", "stop", "tag", "p2a", "term", "gslink", "kdel"}
FROM_BOX = {"goi", "guide"}

# Capsids whose headline property does not transfer to humans.  Selecting one raises a
# dialog in the window; it does not block the design, because they are legitimate choices
# for mouse work.
MOUSE_ONLY_CAPSIDS = {
    "AAV-PHP.eB":
        "AAV-PHP.eB is a mouse research tool.\n\n"
        "It crosses the blood-brain barrier by binding the mouse Ly6a receptor. Humans have "
        "no equivalent receptor serving that role, so the property that makes this capsid "
        "remarkable in mice does not carry over to a human-directed design.\n\n"
        "This is one of the most common ways a striking mouse result fails to translate.\n\n"
        "The design will still be built, and this capsid remains a reasonable choice for "
        "mouse work.",
}

# --------------------------------------------------------------------------
# Sequence helpers
# --------------------------------------------------------------------------

_COMP = {"A": "T", "T": "A", "G": "C", "C": "G", "N": "N"}


def clean_seq(text: str) -> str:
    """Strip FASTA headers, whitespace and digits; uppercase; RNA to DNA."""
    text = re.sub(r"^>.*$", "", text or "", flags=re.MULTILINE)
    return re.sub(r"[\s\d]", "", text).upper().replace("U", "T")


def rev_comp(seq: str) -> str:
    return "".join(_COMP.get(base, "N") for base in reversed(seq))


def count_sites(seq: str, site: str) -> int:
    n, i = 0, seq.find(site)
    while i >= 0:
        n += 1
        i = seq.find(site, i + 1)
    return n


def default_config() -> dict:
    """The configuration the GUI starts from; also used by the test harness."""
    strat = "knock"
    _, targets, prom, mark, _ = STRATEGIES[strat]
    return {
        "vt": "aav", "sero": "AAV9", "route": "intraparenchymal (putamen)", "sc": False,
        "vname": "", "strat": strat, "lib": targets[0], "mut": "", "goi": "", "kozak": True,
        "loc": "intracellular (cytosol)", "deg": "none",
        "gmode": SILENCING[0], "p3": "U6", "greg": REGIONS[0], "gseq": "",
        "prom": prom, "tag": "none", "mark": mark, "link": "P2A",
        "pa": "SV40", "res": "AmpR", "wpre": True, "ov": {},
    }


# --------------------------------------------------------------------------
# The builder: turns a configuration into elements, a sequence and messages
# --------------------------------------------------------------------------

def build(cfg: dict) -> dict:
    """Assemble the vector.  Returns elements, full sequence, name and messages.

    Messages are (level, text) pairs where level is "b" (blocking), "w"
    (warning) or "i" (information).
    """
    t = cfg["vt"]
    features: list[dict] = []
    msgs: list[tuple[str, str]] = []
    overrides = cfg.get("ov") or {}

    def add(fid, name, ftype, length, seq=None):
        features.append({"id": fid, "name": name, "type": ftype,
                         "len": length, "seq": seq, "custom": False})

    strat = cfg["strat"]
    knock = strat == "knock"
    intrabody = strat == "intra"
    sc = t == "aav" and cfg["sc"]

    gene_len, gene_note = GENES.get(cfg["lib"], GENES["Custom"])
    mode = cfg["gmode"]
    sgrna = mode.startswith("sgRNA")
    crispri = mode == "sgRNA (CRISPRi)"
    mirna = mode.startswith("shRNAmir")

    raw = "" if knock else clean_seq(cfg["goi"])
    orf = re.sub(r"[^ACGTN]", "", raw)
    dropped = len(raw) - len(orf)
    target = re.sub(r"[^ACGT]", "", clean_seq(cfg["gseq"])) if knock else ""

    gene = cfg["lib"]
    if gene == "Custom":
        gene = "Target" if knock else "Transgene"
    if gene == "Custom binder":
        gene = "Binder"
    variant = (cfg["mut"] or "").strip()
    if variant and not knock:
        gene += " " + variant

    marker = cfg["mark"]
    linked = "separate PGK promoter" if knock else cfg["link"]
    tag = "none" if knock else cfg["tag"]
    use_p2a = marker != "none" and linked == "P2A"
    loc = cfg["loc"] if intrabody else "intracellular (cytosol)"
    degron = cfg["deg"] if intrabody else "none"
    secreted = loc.startswith("secreted")

    # ---- backbone 5' side ----
    if t == "lenti":
        add("ltr5", "5′ LTR", "ltr", 634)
        add("psi", "Ψ packaging signal", "pack", 124)
        add("rre", "RRE", "pack", 234)
        add("cppt", "cPPT/CTS", "pack", 118)
    if t == "aav":
        add("itr5", "5′ ITR" + (" (ΔTRS mutant)" if sc else ""), "itr", 145)

    # ---- promoter ----
    if knock:
        add("p3", cfg["p3"] + " promoter", "promoter", POL3[cfg["p3"]])
    else:
        add("prom", cfg["prom"] + " promoter", "promoter", PROM[cfg["prom"]])
        if cfg["kozak"]:
            add("kozak", "Kozak", "reg", 6, "GCCACC")

    # ---- payload ----
    if knock:
        spacer = target or "N" * (20 if sgrna else 21)
        if sgrna:
            hairpin = spacer + SGRNA_SCAFFOLD
            label = gene + " sgRNA" + (" (CRISPRi)" if crispri else "")
        elif mirna:
            hairpin = MIR_5P + rev_comp(spacer) + MIR_LOOP + spacer + MIR_3P
            label = gene + " shRNAmir"
        else:
            hairpin = spacer + "TTCAAGAGA" + rev_comp(spacer)
            label = gene + " shRNA"
        add("guide", label, "guide", len(hairpin), hairpin)
        add("term", "Pol III terminator", "polya", 6, "TTTTTT")
    else:
        if secreted:
            add("sp", "IgK signal peptide", "tag", 60)
        add("goi", gene, "cds", len(orf) or gene_len, orf or None)
        if degron != "none":
            add("gslink", "GS linker", "link", len(GS_LINKER), GS_LINKER)
            add("deg", degron + " degron", "tag", DEGRON[degron])
        if loc.startswith("ER-retained"):
            add("kdel", "KDEL retention signal", "tag", len(KDEL_SEQ), KDEL_SEQ)

    if tag != "none":
        add("tag", tag + " tag", "tag", len(TAGS[tag]), TAGS[tag])
    if not use_p2a and not knock:
        add("stop", "Stop (TAA)", "stop", 3, "TAA")

    # ---- reporter / selection ----
    if marker != "none" and not knock:
        if linked == "P2A":
            add("p2a", "P2A", "link", 66, P2A_SEQ)
        if linked == "IRES":
            add("ires", "IRES (EMCV)", "link", 580)
        add("mark", marker, "marker", MARK[marker])
        if use_p2a:
            add("stop", "Stop (TAA)", "stop", 3, "TAA")

    if cfg["wpre"] and not knock:
        add("wpre", "WPRE", "reg", 589)
    if cfg["pa"] != "none" and not knock:
        add("pa", cfg["pa"] + " polyA", "polya", POLYA[cfg["pa"]])
    if marker != "none" and linked.startswith("separate"):
        add("pgk", "PGK promoter", "promoter", 516)
        add("mark2", marker + " (PGK)", "marker", MARK[marker])

    # ---- backbone 3' side ----
    if t == "lenti":
        add("ltr3", "3′ ΔU3 LTR", "ltr", 234)
    if t == "aav":
        add("itr3", "3′ ITR", "itr", 145)
    if t != "plasmid":
        add("f1", "f1 ori", "ori", 429)
    add("res", cfg["res"], "bact", RESIST[cfg["res"]])
    add("ori", "pUC ori", "ori", 589)

    # ---- lay out coordinates and build the sequence ----
    pos, chunks = 1, []
    for f in features:
        custom = overrides.get(f["id"])
        if custom:
            f["seq"] = custom
            f["len"] = len(custom)
            f["custom"] = True
        if not f["seq"]:
            f["seq"] = "N" * f["len"]
        f["s"] = pos
        f["e"] = pos + f["len"] - 1
        pos += f["len"]
        chunks.append(f["seq"])
    sequence = "".join(chunks)
    total = len(sequence)

    # ---- messages: insert sanity ----
    if not knock and not orf:
        msgs.append(("w", f"No sequence pasted, so a {gene_len:,} bp placeholder "
                          f"(typical length) is used for {gene}."))
    if dropped:
        msgs.append(("w", f"{dropped} non-nucleotide character(s) were removed from the ORF."))

    if not knock and orf:
        length = len(orf)
        gc = round(100 * sum(c in "GC" for c in orf) / length)
        if length % 3 == 0:
            stops, first = 0, 0
            for i in range(0, length - 3, 3):
                if orf[i:i + 3] in ("TAA", "TAG", "TGA"):
                    stops += 1
                    if not first:
                        first = i // 3 + 1
            if stops:
                msgs.append(("b", f"{stops} in-frame stop codon(s) inside the sequence; the "
                                  f"first is at codon {first}. Check the reading frame, or "
                                  f"confirm the premature stop is intended."))
        msgs.append(("i", f"Insert: {length:,} bp, {gc}% GC."))
        if t == "lenti" and re.search(r"AATAAA|ATTAAA", orf):
            msgs.append(("w", "The insert contains a polyadenylation signal (AATAAA or "
                              "ATTAAA). In a lentiviral genome this can truncate the vector "
                              "RNA and lower titer."))
        free, cut = [], []
        for name, site in ENZYMES.items():
            n = count_sites(orf, site)
            (cut.append(f"{name} ×{n}") if n else free.append(name))
        msgs.append(("i", "Restriction sites in the insert: none for "
                          + (", ".join(free) or "any listed enzyme")
                          + (". It is cut by " + ", ".join(cut) + "." if cut else ".")))
        if length % 3:
            msgs.append(("w", f"ORF length ({length} bp) is not a multiple of 3."))
        if not orf.startswith("ATG") and not secreted:
            msgs.append(("w", "ORF does not start with ATG."))
        if orf[-3:] in ("TAA", "TAG", "TGA") and length % 3 == 0:
            msgs.append(("w", "ORF ends in a stop codon. Remove it if you use a tag, a "
                              "degron, a KDEL signal or a P2A reporter."))

    if not knock and gene_note:
        msgs.append(("i", gene_note))

    # ---- messages: silencing design ----
    if knock:
        if not target:
            msgs.append(("w", "No target sequence pasted, so an N-filled placeholder is used."))
        elif sgrna and len(target) != 20:
            msgs.append(("w", f"sgRNA protospacers are usually 20 nt (yours: {len(target)})."))
        elif not sgrna and not 19 <= len(target) <= 25:
            msgs.append(("w", f"shRNA sense strands are usually 19 to 25 nt "
                              f"(yours: {len(target)})."))
        if target:
            gc = round(100 * sum(c in "GC" for c in target) / len(target))
            msgs.append(("i", f"Target: {len(target)} nt, {gc}% GC."))
            if gc < 30 or gc > 60:
                msgs.append(("w", f"Target GC content ({gc}%) is outside the usual 30 to 60% "
                                  f"window for efficient silencing."))
            if re.search(r"A{5,}|T{5,}|G{4,}|C{5,}", target):
                msgs.append(("w", "Target contains a long single-base run, which hurts "
                                  "synthesis and silencing. A run of four or more Gs can also "
                                  "terminate Pol III transcription."))
            if sgrna and target[0] != "G":
                msgs.append(("i", f"{cfg['p3']} transcribes best from a 5′ G. Consider "
                                  f"adding one to the spacer."))
        if crispri:
            msgs.append(("i", "CRISPRi design: this vector carries the sgRNA only. Pair it "
                              "with dCas9-KRAB, and site the spacer roughly 50 bp upstream to "
                              "300 bp downstream of the transcription start site."))
            if cfg["greg"] != "promoter / TSS":
                msgs.append(("w", f"CRISPRi acts at the promoter, but the target region is set "
                                  f"to {cfg['greg']}. Switch the region to promoter / TSS."))
        elif sgrna:
            msgs.append(("i", "This vector carries the sgRNA only. Pair it with Cas9 (SaCas9 "
                              "is compact enough for a second AAV). Permanent cutting of SNCA "
                              "is irreversible and cannot be titrated, unlike RNAi."))
            if cfg["greg"] == "3′ UTR":
                msgs.append(("w", "Cutting in the 3′ UTR does not usually disrupt the "
                                  "protein. Target the coding sequence for knockout."))
        else:
            if cfg["greg"] == "promoter / TSS":
                msgs.append(("w", "RNAi acts on the transcript. Move the target into the "
                                  "coding sequence or 3′ UTR."))
            if cfg["greg"] == "3′ UTR":
                msgs.append(("i", "A 3′ UTR target leaves the coding sequence free, so a "
                                  "knockdown-resistant replacement allele can be "
                                  "co-delivered."))
            if mirna:
                msgs.append(("i", "The miR-E scaffold is processed by the endogenous miRNA "
                                  "pathway and gives lower, better tolerated expression than a "
                                  "simple U6-shRNA hairpin, which matters when oversaturation "
                                  "of RISC in neurons is a concern."))
            else:
                msgs.append(("i", "A strong Pol III hairpin can saturate the endogenous miRNA "
                                  "machinery in neurons. Consider the miR-E scaffold, or a "
                                  "weaker promoter (H1 or 7SK), if you see toxicity unrelated "
                                  "to target knockdown."))
        if cfg["lib"] == "SNCA":
            msgs.append(("w", "α-synuclein is required for normal synaptic function. "
                              "Titrate the dose for partial lowering and include a knockdown "
                              "control: complete nigral loss of α-synuclein has produced "
                              "dopaminergic degeneration in rodent and primate studies."))

    # ---- messages: intrabody design ----
    if intrabody:
        msgs.append(("i", "Binder domains export as N until you paste a verified sequence. "
                          "Keep the signal peptide, binder, linker and degron in a single "
                          "reading frame."))
        if secreted:
            msgs.append(("i", "Secreted binder: intercepts extracellular α-synuclein and "
                              "cell-to-cell seeding, but will not reach intracellular Lewy "
                              "bodies. A degradation tag is not useful on a secreted binder."))
        elif degron != "none":
            msgs.append(("i", "Degron fusion: the binder drags bound α-synuclein into the "
                              "proteasome. Expect the binder itself to turn over fast, so "
                              "check expression by function rather than steady-state protein "
                              "level."))
        if secreted and degron != "none":
            msgs.append(("w", "A secretion signal and a cytosolic degron together are "
                              "contradictory. Pick one."))
        if loc.startswith("ER-retained"):
            msgs.append(("i", "KDEL retention holds the binder in the ER, which suits "
                              "interception of α-synuclein on the secretory route rather "
                              "than cytosolic aggregates."))

    # ---- messages: modeling ----
    if strat == "model":
        msgs.append(("i", "Research use only: α-synuclein overexpression to build a model, "
                          "not a therapeutic design. Human SNCA is standard; expect the "
                          "phenotype to depend strongly on titer, serotype and injection "
                          "coordinates."))
        if t == "aav" and cfg["sero"] == "AAV9":
            msgs.append(("i", "For focal nigral models AAV2 or AAV5 give more contained, "
                              "reproducible lesions than the widely spreading AAV9."))

    # ---- messages: promoter choice ----
    if not knock:
        prom = cfg["prom"]
        if prom in ("hSyn1", "CaMKIIa", "TH (2.5 kb)"):
            extra = ""
            if prom == "CaMKIIa":
                extra = " (mainly excitatory forebrain neurons)"
            elif prom.startswith("TH"):
                extra = (" with catecholaminergic selectivity, which is what you want for "
                         "nigral dopaminergic targeting, though the 2.5 kb fragment eats a "
                         "large share of the AAV payload")
            msgs.append(("i", f"{prom} restricts expression to neurons{extra}. Confirm "
                              f"activity in your model system."))
        if prom == "GfaABC1D":
            msgs.append(("w", "GfaABC1D is an astrocyte promoter. For Lewy pathology inside "
                              "neurons, pick hSyn1, CaMKIIa or TH unless you are deliberately "
                              "targeting glia."))
        if prom in ("CMV", "CAG", "EF1a", "CBh", "UbC", "EFS", "PGK"):
            msgs.append(("w", f"{prom} is ubiquitous, so glia and, after systemic dosing, "
                              f"peripheral tissue will also express the transgene. CMV in "
                              f"particular is prone to silencing in neurons over time."))

    # ---- messages: capsid, route, vector class ----
    if t == "aav":
        if cfg["sero"] in MOUSE_ONLY_CAPSIDS:
            msgs.append(("w", cfg["sero"] + " crosses the blood-brain barrier through a mouse "
                              "receptor with no human ortholog serving that role. It is a "
                              "mouse research tool: pick another capsid for any "
                              "human-directed design."))
        msgs.append(("i", f"{cfg['sero']}: {SEROTYPES[cfg['sero']]}"))
        msgs.append(("i", f"{cfg['route']}: {ROUTES[cfg['route']]}"))
        if cfg["route"].startswith("intravenous"):
            msgs.append(("w", "Systemic dosing exposes liver and dorsal root ganglia and "
                              "requires screening for pre-existing anti-capsid antibodies. A "
                              "neuron-specific promoter limits, but does not prevent, "
                              "off-target expression."))
    if t == "lenti":
        msgs.append(("w", "Lentivirus integrates into the host genome. For post-mitotic "
                          "neurons in vivo, AAV is the usual clinical choice; lentivirus "
                          "suits culture, iPSC-derived neurons and stable lines."))

    # ---- messages: packaging capacity ----
    if t != "plasmid":
        edges = [i for i, f in enumerate(features) if f["type"] in ("ltr", "itr")]
        cassette = sum(f["len"] for f in features[edges[0] + 1:edges[-1]])
        if t == "aav":
            limit, near = (2300, 2100) if sc else (4700, 4400)
            label = "about 2.3 kb (scAAV)" if sc else "about 4.7 kb"
            if cassette > limit:
                msgs.append(("b", f"Cassette between the ITRs is {cassette:,} bp, above the "
                                  f"{label} packaging limit. Shorten the promoter, drop the "
                                  f"reporter or WPRE, or use a smaller transgene."))
            elif cassette > near:
                msgs.append(("w", f"Cassette between the ITRs is {cassette:,} bp, close to the "
                                  f"{label} limit."))
            else:
                msgs.append(("i", f"Cassette between the ITRs: {cassette:,} bp "
                                  f"(limit {label})."))
            if sc:
                msgs.append(("i", "scAAV skips second-strand synthesis, giving faster and "
                                  "stronger onset. It suits small payloads such as a nanobody "
                                  "or an shRNA cassette."))
        else:
            if cassette > 8000:
                msgs.append(("w", f"Insert region between the LTRs is {cassette:,} bp. Large "
                                  f"inserts lower lentiviral titer."))
            else:
                msgs.append(("i", f"Insert region between the LTRs: {cassette:,} bp."))

    if use_p2a:
        msgs.append(("i", "P2A selected: keep the ORF (and any tag or degron) in frame with "
                          "P2A and the reporter."))

    # ---- name ----
    prefix = {"lenti": "pLV", "aav": "pscAAV" if sc else "pAAV", "plasmid": "pEx"}[t]
    driver = cfg["p3"] if knock else re.sub(r"\s*\(.*\)", "", cfg["prom"])
    kind = ("sg" if sgrna else "shmir" if mirna else "sh") if knock else ""
    parts = [f"{prefix}-{driver}>{kind}{gene.replace(' ', '_')}"]
    if degron != "none":
        parts.append("-" + re.sub(r"\s*\(.*\)", "", degron).replace(" ", ""))
    if tag != "none":
        parts.append("-" + tag)
    if marker != "none":
        via = "P2A" if linked == "P2A" else "IRES" if linked == "IRES" else "PGK"
        parts.append(f"-{via}-{marker}")
    name = (cfg["vname"] or "").strip() or "".join(parts)

    msgs.sort(key=lambda m: "bwi".index(m[0]))
    return {"F": features, "seq": sequence, "total": total, "name": name,
            "msgs": msgs, "t": t}


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------

_ASCII = {"′": "'", "Ψ": "psi", "Δ": "d", "α": "a", "β": "b",
          "×": "x", "…": "...", '"': ""}


def ascii_safe(text: str) -> str:
    for src, dst in _ASCII.items():
        text = text.replace(src, dst)
    return text


def genbank(d: dict) -> str:
    today = datetime.date.today()
    month = ("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())[today.month - 1]
    locus = re.sub(r"[^\w>.-]", "_", ascii_safe(d["name"]))[:16]
    out = [f"LOCUS       {locus:<16} {d['total']:>7} bp    DNA     circular SYN "
           f"{today.day:02d}-{month}-{today.year}",
           f"DEFINITION  {ascii_safe(d['name'])}, designed with {APP_TITLE}.",
           "FEATURES             Location/Qualifiers"]
    for f in d["F"]:
        out.append(f"     {GB_KEYS[f['type']]:<16}{f['s']}..{f['e']}")
        out.append(f"                     /label=\"{ascii_safe(f['name'])}\"")
    out.append("ORIGIN")
    seq = d["seq"].lower()
    for i in range(0, d["total"], 60):
        block = " ".join(seq[j:j + 10] for j in range(i, min(i + 60, d["total"]), 10))
        out.append(f"{i + 1:>9} {block}")
    out.append("//")
    return "\n".join(out) + "\n"


def fasta(d: dict) -> str:
    seq = d["seq"]
    lines = [seq[i:i + 70] for i in range(0, len(seq), 70)]
    header = f">{ascii_safe(d['name']).replace(' ', '_')} {d['total']} bp circular"
    return "\n".join([header] + lines) + "\n"


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------

THEMES = {
    "light": {"bg": "#eff1f7", "card": "#ffffff", "tx": "#171a2b", "mut": "#5f6782",
              "bd": "#d7dae8", "ac": "#5245a8", "acx": "#ffffff", "soft": "#eae7f7",
              "warn": "#9a5a00", "bad": "#b3261e", "field": "#ffffff"},
    "dark": {"bg": "#101220", "card": "#1a1d2e", "tx": "#e8eaf4", "mut": "#9aa2bd",
             "bd": "#2f3350", "ac": "#9a8cf0", "acx": "#14102b", "soft": "#241f45",
             "warn": "#f0a548", "bad": "#ff8a80", "field": "#232740"},
}


def main() -> None:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, simpledialog

    class Designer(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title(APP_TITLE)
            self.geometry("1320x900")
            self.minsize(1000, 680)
            self.theme = "light"
            self.cfg = default_config()
            self.var: dict[str, tk.Variable] = {}
            self.current: dict | None = None
            self.row_ids: dict[str, str] = {}
            self._capsid_warned = False
            self._painted: list[tuple[tk.Widget, str]] = []
            self.style = ttk.Style(self)
            try:
                self.style.theme_use("clam")
            except tk.TclError:
                pass
            self._build_ui()
            self.apply_theme()
            self.on_strategy()

        # ---------------- theming ----------------
        def paint(self, widget, role):
            self._painted.append((widget, role))
            return widget

        def apply_theme(self):
            p = THEMES[self.theme]
            s, cfg = self.style, self.style.configure
            self.configure(bg=p["bg"])
            cfg(".", background=p["bg"], foreground=p["tx"], fieldbackground=p["field"],
                bordercolor=p["bd"], lightcolor=p["bd"], darkcolor=p["bd"])
            cfg("TFrame", background=p["bg"])
            cfg("Card.TFrame", background=p["card"], relief="solid", borderwidth=1)
            cfg("TLabel", background=p["card"], foreground=p["tx"])
            cfg("Bg.TLabel", background=p["bg"], foreground=p["tx"])
            cfg("H1.TLabel", background=p["bg"], foreground=p["tx"],
                font=("TkDefaultFont", 17, "bold"))
            cfg("Sub.TLabel", background=p["bg"], foreground=p["mut"])
            cfg("Head.TLabel", background=p["card"], foreground=p["tx"],
                font=("TkDefaultFont", 10, "bold"))
            cfg("Field.TLabel", background=p["card"], foreground=p["mut"])
            cfg("Note.TLabel", background=p["card"], foreground=p["mut"])
            cfg("TCheckbutton", background=p["card"], foreground=p["tx"])
            cfg("TRadiobutton", background=p["card"], foreground=p["tx"])
            cfg("TButton", background=p["ac"], foreground=p["acx"], borderwidth=1,
                focuscolor=p["ac"], padding=(10, 5))
            s.map("TButton", background=[("active", p["ac"]), ("pressed", p["ac"])],
                  foreground=[("active", p["acx"])])
            cfg("Ghost.TButton", background=p["card"], foreground=p["ac"])
            s.map("Ghost.TButton", background=[("active", p["soft"])],
                  foreground=[("active", p["ac"])])
            cfg("TEntry", fieldbackground=p["field"], foreground=p["tx"],
                insertcolor=p["tx"], padding=3)
            cfg("TCombobox", fieldbackground=p["field"], foreground=p["tx"],
                background=p["card"], arrowcolor=p["tx"], padding=3)
            s.map("TCombobox", fieldbackground=[("readonly", p["field"])],
                  foreground=[("readonly", p["tx"])])
            cfg("Treeview", background=p["card"], fieldbackground=p["card"],
                foreground=p["tx"], rowheight=23, borderwidth=0)
            cfg("Treeview.Heading", background=p["bg"], foreground=p["mut"],
                relief="flat")
            s.map("Treeview", background=[("selected", p["soft"])],
                  foreground=[("selected", p["tx"])])
            cfg("TScrollbar", background=p["card"], troughcolor=p["bg"],
                arrowcolor=p["mut"])
            self.option_add("*TCombobox*Listbox.background", p["field"])
            self.option_add("*TCombobox*Listbox.foreground", p["tx"])
            self.option_add("*TCombobox*Listbox.selectBackground", p["ac"])
            self.option_add("*TCombobox*Listbox.selectForeground", p["acx"])

            for widget, role in self._painted:
                try:
                    if role == "canvas":
                        widget.configure(bg=p["card"], highlightthickness=0)
                    elif role == "scroll_canvas":
                        widget.configure(bg=p["card"], highlightthickness=0)
                    elif role == "text":
                        widget.configure(bg=p["field"], fg=p["tx"], insertbackground=p["tx"],
                                         highlightbackground=p["bd"],
                                         selectbackground=p["soft"], selectforeground=p["tx"])
                    elif role == "msgs":
                        widget.configure(bg=p["card"], fg=p["tx"], highlightthickness=0,
                                         selectbackground=p["soft"])
                except tk.TclError:
                    pass
            self.msgs.tag_configure("i", background=p["soft"], foreground=p["tx"],
                                    lmargin1=8, lmargin2=8, spacing1=3, spacing3=3)
            self.msgs.tag_configure("w", foreground=p["warn"], lmargin1=8, lmargin2=8,
                                    spacing1=3, spacing3=3)
            self.msgs.tag_configure("b", foreground=p["bad"], lmargin1=8, lmargin2=8,
                                    spacing1=3, spacing3=3)
            self.theme_btn.configure(text="Dark theme" if self.theme == "light"
                                     else "Light theme")
            if self.current:
                self.render()

        def toggle_theme(self):
            self.theme = "dark" if self.theme == "light" else "light"
            self.apply_theme()

        # ---------------- widget helpers ----------------
        def heading(self, parent, text, row):
            ttk.Label(parent, text=text, style="Head.TLabel").grid(
                row=row, column=0, sticky="w", pady=(12, 4))

        def combo(self, parent, key, label, values, row, column=0, width=None, cmd=None):
            box = ttk.Frame(parent, style="Card.TFrame")
            box.configure(borderwidth=0)
            box.grid(row=row, column=column, sticky="ew", padx=(0, 6), pady=2)
            box.columnconfigure(0, weight=1)
            ttk.Label(box, text=label, style="Field.TLabel").grid(row=0, column=0, sticky="w")
            var = self.var.setdefault(key, tk.StringVar(value=self.cfg[key]))
            widget = ttk.Combobox(box, textvariable=var, values=list(values),
                                  state="readonly", width=width or 18)
            widget.grid(row=1, column=0, sticky="ew")
            widget.bind("<<ComboboxSelected>>", cmd or (lambda _e: self.render()))
            return box, widget

        def entry(self, parent, key, label, row, placeholder=""):
            box = ttk.Frame(parent, style="Card.TFrame")
            box.configure(borderwidth=0)
            box.grid(row=row, column=0, columnspan=2, sticky="ew", pady=2)
            box.columnconfigure(0, weight=1)
            ttk.Label(box, text=label, style="Field.TLabel").grid(row=0, column=0, sticky="w")
            var = self.var.setdefault(key, tk.StringVar(value=self.cfg[key]))
            field = ttk.Entry(box, textvariable=var)
            field.grid(row=1, column=0, sticky="ew")
            var.trace_add("write", lambda *_: self.render())
            if placeholder:
                ttk.Label(box, text=placeholder, style="Note.TLabel",
                          wraplength=360).grid(row=2, column=0, sticky="w")
            return box

        def check(self, parent, key, label, row, cmd=None):
            var = self.var.setdefault(key, tk.BooleanVar(value=self.cfg[key]))
            widget = ttk.Checkbutton(parent, text=label, variable=var,
                                     command=cmd or self.render)
            widget.grid(row=row, column=0, columnspan=2, sticky="w", pady=(6, 2))
            return widget

        # ---------------- layout ----------------
        def _build_ui(self):
            head = ttk.Frame(self)
            head.pack(fill="x", padx=18, pady=(14, 2))
            ttk.Label(head, text=APP_TITLE, style="H1.TLabel").pack(side="left")
            self.theme_btn = ttk.Button(head, text="Dark theme", style="Ghost.TButton",
                                        command=self.toggle_theme)
            self.theme_btn.pack(side="right")
            ttk.Label(self, text=APP_SUB, style="Sub.TLabel", wraplength=1200,
                      justify="left").pack(fill="x", padx=18, pady=(0, 8))

            body = ttk.Frame(self)
            body.pack(fill="both", expand=True, padx=14, pady=(0, 12))
            body.columnconfigure(0, minsize=430)
            body.columnconfigure(1, weight=1)
            body.rowconfigure(0, weight=1)

            self._build_left(body)
            self._build_right(body)

        def _build_left(self, body):
            shell = ttk.Frame(body, style="Card.TFrame")
            shell.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
            shell.rowconfigure(0, weight=1)
            shell.columnconfigure(0, weight=1)

            canvas = self.paint(tk.Canvas(shell, width=400, borderwidth=0), "scroll_canvas")
            canvas.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=10)
            bar = ttk.Scrollbar(shell, orient="vertical", command=canvas.yview)
            bar.grid(row=0, column=1, sticky="ns", pady=10, padx=(2, 4))
            canvas.configure(yscrollcommand=bar.set)

            panel = ttk.Frame(canvas, style="Card.TFrame")
            panel.configure(borderwidth=0)
            window = canvas.create_window((0, 0), window=panel, anchor="nw")
            panel.bind("<Configure>",
                       lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.bind("<Configure>",
                        lambda e: canvas.itemconfigure(window, width=e.width - 4))

            def wheel(event):
                step = -1 * (event.delta // 120) if abs(event.delta) >= 120 else -event.delta
                canvas.yview_scroll(step, "units")
            canvas.bind_all("<MouseWheel>", wheel)
            canvas.bind_all("<Button-4>", lambda _e: canvas.yview_scroll(-3, "units"))
            canvas.bind_all("<Button-5>", lambda _e: canvas.yview_scroll(3, "units"))

            panel.columnconfigure(0, weight=1)
            panel.columnconfigure(1, weight=1)
            r = 0

            self.heading(panel, "Vector type", r); r += 1
            vt_row = ttk.Frame(panel, style="Card.TFrame")
            vt_row.configure(borderwidth=0)
            vt_row.grid(row=r, column=0, columnspan=2, sticky="ew"); r += 1
            self.var["vt"] = tk.StringVar(value=self.cfg["vt"])
            for i, (val, text) in enumerate((("aav", "AAV"), ("lenti", "Lentivirus"),
                                             ("plasmid", "Plasmid"))):
                ttk.Radiobutton(vt_row, text=text, value=val, variable=self.var["vt"],
                                command=self.on_vector).grid(row=0, column=i, sticky="w",
                                                             padx=(0, 14))

            self.aav_box = ttk.Frame(panel, style="Card.TFrame")
            self.aav_box.configure(borderwidth=0)
            self.aav_box.grid(row=r, column=0, columnspan=2, sticky="ew"); r += 1
            self.aav_box.columnconfigure(0, weight=1)
            self.aav_box.columnconfigure(1, weight=1)
            self.combo(self.aav_box, "sero", "Capsid / serotype", SEROTYPES, 0, 0,
                       cmd=self.on_serotype)
            self.combo(self.aav_box, "route", "Delivery route", ROUTES, 0, 1)
            self.check(self.aav_box, "sc",
                       "Self-complementary (scAAV): faster onset, about half the capacity", 1)

            self.entry(panel, "vname", "Vector name (optional)", r,
                       "Left empty, a name is generated from your choices."); r += 1

            self.heading(panel, "Therapeutic strategy", r); r += 1
            names = [v[0] for v in STRATEGIES.values()]
            self.strat_keys = {v[0]: k for k, v in STRATEGIES.items()}
            self.var["strat_name"] = tk.StringVar(value=STRATEGIES[self.cfg["strat"]][0])
            strat_box = ttk.Frame(panel, style="Card.TFrame")
            strat_box.configure(borderwidth=0)
            strat_box.grid(row=r, column=0, columnspan=2, sticky="ew", pady=2); r += 1
            strat_box.columnconfigure(0, weight=1)
            ttk.Label(strat_box, text="Strategy", style="Field.TLabel").grid(
                row=0, column=0, sticky="w")
            strat_combo = ttk.Combobox(strat_box, textvariable=self.var["strat_name"],
                                       values=names, state="readonly")
            strat_combo.grid(row=1, column=0, sticky="ew")
            strat_combo.bind("<<ComboboxSelected>>", lambda _e: self.on_strategy())
            self.tip = ttk.Label(strat_box, text="", style="Note.TLabel", wraplength=370,
                                 justify="left")
            self.tip.grid(row=2, column=0, sticky="w", pady=(4, 0))

            _, self.lib_combo = self.combo(panel, "lib", "Target / transgene", [], r,
                                           0, width=24)
            r += 1
            self.entry(panel, "mut", "Variant label (optional)", r,
                       "For example A53T, A30P, E46K, D620N."); r += 1

            self.orf_box = ttk.Frame(panel, style="Card.TFrame")
            self.orf_box.configure(borderwidth=0)
            self.orf_box.grid(row=r, column=0, columnspan=2, sticky="ew", pady=(6, 0)); r += 1
            self.orf_box.columnconfigure(0, weight=1)
            self.orf_label = ttk.Label(self.orf_box, text="ORF sequence", style="Field.TLabel")
            self.orf_label.grid(row=0, column=0, sticky="w")
            self.orf_text = self.paint(
                tk.Text(self.orf_box, height=6, wrap="char", relief="solid", borderwidth=1,
                        font=("TkFixedFont", 9)), "text")
            self.orf_text.grid(row=1, column=0, sticky="ew")
            self.orf_text.bind("<KeyRelease>", lambda _e: self.render())
            ttk.Label(self.orf_box, style="Note.TLabel", wraplength=370, justify="left",
                      text=("Paste DNA or FASTA from NCBI or CCDS. With no sequence, a "
                            "typical-length placeholder is used.")).grid(row=2, column=0,
                                                                         sticky="w")
            self.check(self.orf_box, "kozak",
                       "Add Kozak sequence (GCCACC) before the ORF", 3)

            self.ib_box = ttk.Frame(panel, style="Card.TFrame")
            self.ib_box.configure(borderwidth=0)
            self.ib_box.grid(row=r, column=0, columnspan=2, sticky="ew"); r += 1
            self.ib_box.columnconfigure(0, weight=1)
            self.ib_box.columnconfigure(1, weight=1)
            self.combo(self.ib_box, "loc", "Localization", LOCAL, 0, 0)
            self.combo(self.ib_box, "deg", "Degradation tag", DEGRON, 0, 1)

            self.guide_box = ttk.Frame(panel, style="Card.TFrame")
            self.guide_box.configure(borderwidth=0)
            self.guide_box.grid(row=r, column=0, columnspan=2, sticky="ew"); r += 1
            self.guide_box.columnconfigure(0, weight=1)
            self.guide_box.columnconfigure(1, weight=1)
            self.combo(self.guide_box, "gmode", "Silencing format", SILENCING, 0, 0)
            self.combo(self.guide_box, "p3", "Pol III promoter", POL3, 0, 1)
            greg_box, _ = self.combo(self.guide_box, "greg", "Target region", REGIONS, 1, 0)
            greg_box.grid(columnspan=2)
            gseq_box = self.entry(self.guide_box, "gseq", "Target sequence", 2,
                                  ("shRNA: 19 to 25 nt sense strand. "
                                   "sgRNA: 20 nt protospacer, no PAM."))
            gseq_box.grid(row=2, column=0, columnspan=2, sticky="ew")

            self.heading(panel, "Expression", r); r += 1
            exp = ttk.Frame(panel, style="Card.TFrame")
            exp.configure(borderwidth=0)
            exp.grid(row=r, column=0, columnspan=2, sticky="ew"); r += 1
            exp.columnconfigure(0, weight=1)
            exp.columnconfigure(1, weight=1)
            self.prom_box, _ = self.combo(exp, "prom", "Promoter", PROM, 0, 0)
            self.tag_box, _ = self.combo(exp, "tag", "C-terminal tag", TAGS, 0, 1)
            self.combo(exp, "mark", "Reporter / selection", MARK, 1, 0,
                       cmd=lambda _e: self.on_strategy(keep=True))
            self.link_box, _ = self.combo(exp, "link", "Linked by", LINK, 1, 1)
            self.combo(exp, "pa", "Polyadenylation", POLYA, 2, 0)
            self.combo(exp, "res", "Bacterial selection", RESIST, 2, 1)
            self.check(exp, "wpre", "Include WPRE", 3)

            ttk.Label(panel, style="Note.TLabel", wraplength=380, justify="left",
                      text=("Research design tool. Producing virus requires institutional "
                            "biosafety approval, and clinical gene therapy products need GMP "
                            "manufacturing, preclinical safety and efficacy data, and "
                            "regulatory authorization.")).grid(row=r, column=0, columnspan=2,
                                                               sticky="w", pady=(14, 4))

        def _build_right(self, body):
            card = ttk.Frame(body, style="Card.TFrame")
            card.grid(row=0, column=1, sticky="nsew")
            card.columnconfigure(0, weight=1)
            card.rowconfigure(1, weight=1)
            card.rowconfigure(4, weight=1)

            self.msgs = self.paint(
                tk.Text(card, height=9, wrap="word", relief="flat", borderwidth=0,
                        state="disabled", cursor="arrow"), "msgs")
            self.msgs.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))

            middle = ttk.Frame(card, style="Card.TFrame")
            middle.configure(borderwidth=0)
            middle.grid(row=1, column=0, sticky="nsew", padx=14)
            middle.columnconfigure(1, weight=1)
            middle.rowconfigure(0, weight=1)

            self.map = self.paint(tk.Canvas(middle, width=330, height=330,
                                            borderwidth=0), "canvas")
            self.map.grid(row=0, column=0, sticky="n", padx=(0, 12))

            tree_wrap = ttk.Frame(middle, style="Card.TFrame")
            tree_wrap.configure(borderwidth=0)
            tree_wrap.grid(row=0, column=1, sticky="nsew")
            tree_wrap.columnconfigure(0, weight=1)
            tree_wrap.rowconfigure(0, weight=1)
            self.tree = ttk.Treeview(tree_wrap, columns=("pos", "bp", "seq"),
                                     show="tree headings", selectmode="browse")
            self.tree.heading("#0", text="Element")
            self.tree.heading("pos", text="Position")
            self.tree.heading("bp", text="bp")
            self.tree.heading("seq", text="Sequence")
            self.tree.column("#0", width=215, stretch=True)
            self.tree.column("pos", width=92, anchor="e", stretch=False)
            self.tree.column("bp", width=58, anchor="e", stretch=False)
            self.tree.column("seq", width=170, stretch=True)
            self.tree.grid(row=0, column=0, sticky="nsew")
            tbar = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
            tbar.grid(row=0, column=1, sticky="ns")
            self.tree.configure(yscrollcommand=tbar.set)
            self.tree.bind("<Double-1>", self.edit_element)
            self.tree.bind("<Return>", self.edit_element)

            self.foot = ttk.Label(card, text="", style="Note.TLabel")
            self.foot.grid(row=2, column=0, sticky="w", padx=14, pady=(8, 0))

            btns = ttk.Frame(card, style="Card.TFrame")
            btns.configure(borderwidth=0)
            btns.grid(row=3, column=0, sticky="w", padx=14, pady=(8, 4))
            ttk.Button(btns, text="Copy GenBank",
                       command=lambda: self.copy(genbank)).pack(side="left", padx=(0, 8))
            ttk.Button(btns, text="Copy FASTA", style="Ghost.TButton",
                       command=lambda: self.copy(fasta)).pack(side="left", padx=(0, 8))
            ttk.Button(btns, text="Save GenBank…", style="Ghost.TButton",
                       command=lambda: self.save(genbank, ".gb")).pack(side="left", padx=(0, 8))
            ttk.Button(btns, text="Save FASTA…", style="Ghost.TButton",
                       command=lambda: self.save(fasta, ".fa")).pack(side="left")

            out_wrap = ttk.Frame(card, style="Card.TFrame")
            out_wrap.configure(borderwidth=0)
            out_wrap.grid(row=4, column=0, sticky="nsew", padx=14, pady=(4, 6))
            out_wrap.columnconfigure(0, weight=1)
            out_wrap.rowconfigure(1, weight=1)
            ttk.Label(out_wrap, text="Sequence file", style="Field.TLabel").grid(
                row=0, column=0, sticky="w")
            self.out = self.paint(tk.Text(out_wrap, height=9, wrap="none", relief="solid",
                                          borderwidth=1, font=("TkFixedFont", 9)), "text")
            self.out.grid(row=1, column=0, sticky="nsew")
            obar = ttk.Scrollbar(out_wrap, orient="vertical", command=self.out.yview)
            obar.grid(row=1, column=1, sticky="ns")
            self.out.configure(yscrollcommand=obar.set)

            ttk.Label(card, style="Note.TLabel", wraplength=700, justify="left",
                      text=("Element lengths are typical values. Elements without a built-in "
                            "sequence export as N: double-click a row to paste a verified "
                            "sequence, for example from an Addgene reference plasmid."),
                      ).grid(row=5, column=0, sticky="w", padx=14, pady=(0, 12))

        # ---------------- state ----------------
        def collect(self) -> dict:
            cfg = dict(self.cfg)
            for key, var in self.var.items():
                if key == "strat_name":
                    continue
                cfg[key] = var.get()
            cfg["strat"] = self.strat_keys[self.var["strat_name"].get()]
            cfg["goi"] = self.orf_text.get("1.0", "end-1c")
            cfg["ov"] = self.cfg.get("ov", {})
            return cfg

        def on_vector(self):
            vt = self.var["vt"].get()
            if vt == "aav":
                self.aav_box.grid()
            else:
                self.aav_box.grid_remove()
            self.var["wpre"].set(vt != "plasmid")
            self.var["pa"].set("bGH" if vt == "plasmid" else "SV40")
            self.check_capsid()
            self.render()

        def on_serotype(self, _event=None):
            self.check_capsid()
            self.render()

        def check_capsid(self):
            """Raise a dialog on entering a mouse-only capsid; once per entry, not per edit."""
            capsid = self.var["sero"].get()
            mouse_only = self.var["vt"].get() == "aav" and capsid in MOUSE_ONLY_CAPSIDS
            if mouse_only and not self._capsid_warned:
                self._capsid_warned = True
                messagebox.showwarning(APP_TITLE, MOUSE_ONLY_CAPSIDS[capsid], parent=self)
            elif not mouse_only:
                self._capsid_warned = False

        def on_strategy(self, keep=False):
            key = self.strat_keys[self.var["strat_name"].get()]
            name, targets, prom, mark, tip = STRATEGIES[key]
            knock = key == "knock"
            if not keep:
                self.lib_combo.configure(values=targets)
                if self.var["lib"].get() not in targets:
                    self.var["lib"].set(targets[0])
                self.var["prom"].set(prom)
                self.var["mark"].set(mark)
            self.tip.configure(text=tip)
            (self.guide_box.grid() if knock else self.guide_box.grid_remove())
            (self.orf_box.grid_remove() if knock else self.orf_box.grid())
            (self.ib_box.grid() if key == "intra" else self.ib_box.grid_remove())
            (self.prom_box.grid_remove() if knock else self.prom_box.grid())
            (self.tag_box.grid_remove() if knock else self.tag_box.grid())
            hide_link = knock or self.var["mark"].get() == "none"
            (self.link_box.grid_remove() if hide_link else self.link_box.grid())
            self.orf_label.configure(
                text=("Binder sequence (nanobody, or scFv as VH–linker–VL)"
                      if key == "intra" else
                      "ORF sequence (start with ATG, omit the stop codon)"))
            self.render()

        # ---------------- drawing ----------------
        def render(self):
            p = THEMES[self.theme]
            data = self.current = build(self.collect())

            self.msgs.configure(state="normal")
            self.msgs.delete("1.0", "end")
            for level, text in data["msgs"]:
                prefix = {"b": "✕  ", "w": "!  ", "i": ""}[level]
                self.msgs.insert("end", prefix + text + "\n", level)
            self.msgs.configure(state="disabled")

            self.draw_map(data, p)

            keep = self.row_ids.get(self.tree.focus())
            self.tree.delete(*self.tree.get_children())
            self.row_ids.clear()
            by_element = {}
            for f in data["F"]:
                if f["id"] in FROM_BOX:
                    cell = "from the sequence box"
                elif f["id"] in BUILT_IN:
                    cell = "built in"
                elif f["custom"]:
                    cell = f["seq"] if len(f["seq"]) <= 24 else f["seq"][:21] + "…"
                else:
                    cell = "double-click to paste"
                iid = self.tree.insert("", "end", text="  " + f["name"],
                                       values=(f"{f['s']}..{f['e']}", f["len"], cell),
                                       tags=(f["type"],))
                self.row_ids[iid] = f["id"]
                by_element[f["id"]] = iid
            for ftype, color in COLORS.items():
                self.tree.tag_configure(ftype, foreground=color)
            if keep in by_element:          # keep the row selected across redraws
                self.tree.focus(by_element[keep])
                self.tree.selection_set(by_element[keep])

            self.foot.configure(text=f"{data['name']}  ·  {data['total']:,} bp  "
                                     f"·  {len(data['F'])} elements")
            self.out.configure(state="normal")
            self.out.delete("1.0", "end")
            self.out.insert("1.0", genbank(data))
            self.out.configure(state="disabled")

        def draw_map(self, data, p):
            c = self.map
            c.delete("all")
            w, h = int(c.winfo_width()), int(c.winfo_height())
            if w < 60:          # before the first layout pass
                w = 330
            if h < 60:
                h = 330
            size = max(220, min(w, h))
            cx = cy = size / 2
            r, thick = size * 0.37, max(14, size * 0.075)
            box = (cx - r, cy - r, cx + r, cy + r)
            c.create_oval(*box, outline=p["bd"], width=thick)
            total = max(1, data["total"])
            for f in data["F"]:
                start = 90 - 360 * (f["s"] - 1) / total
                extent = -360 * f["len"] / total
                if abs(extent) < 0.9:
                    extent = -0.9
                c.create_arc(*box, start=start, extent=extent, style="arc",
                             outline=COLORS[f["type"]], width=thick)
            c.create_line(cx, cy - r - thick / 2, cx, cy - r - thick / 2 - 9, fill=p["tx"])
            c.create_text(cx + 8, cy - r - thick - 6, text="1", fill=p["mut"],
                          anchor="w", font=("TkDefaultFont", 8))
            name = data["name"]
            if len(name) > 28:
                name = name[:27] + "…"
            c.create_text(cx, cy - 9, text=name, fill=p["tx"],
                          font=("TkDefaultFont", 10, "bold"))
            c.create_text(cx, cy + 12, text=f"{data['total']:,} bp", fill=p["mut"],
                          font=("TkDefaultFont", 9))

        # ---------------- actions ----------------
        def edit_element(self, _event=None):
            selected = self.tree.focus()
            if not selected:
                return
            fid = self.row_ids.get(selected)
            if fid in FROM_BOX or fid in BUILT_IN:
                messagebox.showinfo(
                    APP_TITLE,
                    "This element comes from the sequence box or is built in, so it is not "
                    "edited here.")
                return
            feature = next((f for f in self.current["F"] if f["id"] == fid), None)
            if feature is None:
                return
            answer = simpledialog.askstring(
                "Paste sequence",
                f"Verified sequence for {feature['name']}\n"
                f"(leave empty to go back to {feature['len']} bp of N):",
                initialvalue=self.cfg["ov"].get(fid, ""), parent=self)
            if answer is None:
                return
            cleaned = re.sub(r"[^ACGTN]", "", clean_seq(answer))
            if cleaned:
                self.cfg["ov"][fid] = cleaned
            else:
                self.cfg["ov"].pop(fid, None)
            self.render()

        def copy(self, formatter):
            if not self.current:
                return
            self.clipboard_clear()
            self.clipboard_append(formatter(self.current))
            self.update()
            self.foot.configure(text=f"Copied {formatter.__name__.upper()} to the clipboard.")
            self.after(1800, self.render)

        def save(self, formatter, suffix):
            if not self.current:
                return
            stem = re.sub(r"[^\w.-]", "_", ascii_safe(self.current["name"]))
            path = filedialog.asksaveasfilename(
                parent=self, defaultextension=suffix, initialfile=stem + suffix,
                filetypes=[("GenBank", "*.gb *.gbk"), ("FASTA", "*.fa *.fasta"),
                           ("All files", "*.*")])
            if not path:
                return
            try:
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(formatter(self.current))
            except OSError as err:
                messagebox.showerror(APP_TITLE, f"Could not write the file:\n{err}")
                return
            self.foot.configure(text=f"Saved {path}")
            self.after(2500, self.render)

    app = Designer()
    app.map.bind("<Configure>", lambda _e: app.render())
    app.mainloop()


if __name__ == "__main__":
    main()

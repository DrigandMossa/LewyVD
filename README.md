# Lewy Body Gene Therapy Vector Designer

A desktop tool for designing gene therapy vectors aimed at the protein clumps that build up
inside brain cells in Parkinson's disease and Lewy body dementia.

```bash
python3 lewy_vector_designer.py
```

That's the whole installation. One file, no `pip install`, nothing downloaded.

---

## Start here: what this is, in plain language

No biology background needed for this section. If you already know the field, skip to
[Running it](#running-it).

### The problem

Inside your brain cells there's a protein called **alpha-synuclein** (say "AL-fa
sin-NEW-clee-in"). Normally it drifts around loose and does useful work where nerve cells
pass signals to each other.

In Parkinson's disease it starts sticking to itself. One clump catches a second, those two
catch two more, and the clumps keep growing until the cell is full of lumps called **Lewy
bodies**. The brain cells that make dopamine — the chemical you need to move smoothly — are
hit first and die. That's where the tremor and the stiffness come from.

The awkward part is that the stuck-together form is the one the protein actually *prefers*.
A healthy cell isn't safe because clumping is impossible; it's safe because it keeps three
defences running every second of your life:

- **Stopping clumps from starting.** The first clump is the hard one to form, and the cell
  works to keep it that way.
- **Chaperones.** Helper proteins that catch a badly-folded protein and hold it in the right
  shape before it can stick to anything.
- **Clearance.** A disposal system that finds clumps and digests them back into parts.

All three fade as you get older, which is a large part of why this is a disease of older
people. The goal isn't to invent a fourth defence. It's to top one of the three back up.

### What a gene therapy vector is

Your cells build proteins by following instructions written in DNA. One instruction for one
protein is a **gene**.

Gene therapy means getting an extra copy of a useful instruction into someone's cells so they
build more of a helpful protein. The hard part is delivery, and the best delivery device
turns out to be a virus — because getting inside cells is the one thing viruses are
exceptional at.

So you take a harmless virus called **AAV**, strip out all of its own genes, and load your
instruction into the empty shell. Think of it as a delivery van. The shell is the van, your
gene is the cargo, and everything that made it a virus is gone.

Three things about the van matter, and this program tracks all three:

- **It's tiny.** Roughly 4,700 letters of DNA fit inside, and that's everything — your gene
  plus every switch and label around it. This single number shapes the whole field.
- **It needs an address.** The outside of the shell is the **capsid**, and it decides which
  cells the van can get into.
- **It needs an on-switch.** A **promoter** sits in front of the gene and tells the cell when
  and where to read it. A good one means "switch on in neurons, stay off everywhere else."

### What this program does

It designs one of those vans on paper and writes out the exact DNA sequence, in file formats
real labs use.

It does not make anything. Nothing on your laptop can. Making a real vector needs a licensed
facility and biosafety approval; treating a person with one needs years of testing and
government permission. This is the drawing-board step — which is genuinely useful, and also
nowhere near the finish line.

---

## Running it

You need **Python 3.9 or newer**, plus a graphics add-on called `tkinter`:

| System | What to do |
|---|---|
| Windows, macOS | Nothing — `tkinter` comes with the installer from [python.org](https://www.python.org/downloads/) |
| Debian, Ubuntu | `sudo apt install python3-tk` |
| Fedora | `sudo dnf install python3-tkinter` |

Then:

```bash
python3 lewy_vector_designer.py
```

A window opens. There's no command-line mode — this program is the window.

The window has **controls down the left**, and on the right, from top to bottom: a
**messages** panel, a **circular map** of your design, a **table** of its parts, the export
buttons, and the finished sequence file. There's a **Dark theme** button in the top right.

Everything updates the instant you change anything. You can't break it, and nothing is saved
until you press a save button, so click around freely.

---

## The six strategies

The **Strategy** dropdown is the main decision. Each one is a different way to help, and each
comes with its own list of targets.

| Strategy | The idea, plainly | Default target |
|---|---|---|
| **α-synuclein lowering** | Make less of the protein in the first place. Fewer copies, less clumping | `SNCA` |
| **Intrabody or nanobody** | Build a tiny gripper that grabs alpha-synuclein and stops it sticking to its neighbours | `NbSyn87` |
| **Lysosomal and autophagic clearance** | Upgrade the cell's disposal system so it digests clumps faster | `GBA1` |
| **Chaperone and proteostasis** | Supply more of the helpers that hold proteins in the right shape | `DNAJB6` |
| **Neurotrophic and symptomatic** | Support the surviving neurons, or restore dopamine production | `GDNF` |
| **α-synucleinopathy modeling** | Deliberately *cause* the problem in lab animals, to study it | `SNCA` |

Two of those deserve a flag.

**Neurotrophic support doesn't touch the clumps.** It helps tired neurons stay alive. That's
worth something, but it's a different job, and the program says so when you pick it.

**Modeling is not a treatment.** It's the standard way researchers give a rat Parkinson's-like
damage so they have something to test treatments on. The program labels every modeling design
as research-use-only, because a design that causes the disease and a design that treats it
look almost identical on screen.

### Lowering: four ways to do it

Pick **α-synuclein lowering** and a second dropdown appears with four methods:

| Method | What it does |
|---|---|
| `shRNA` | Shreds the message before the protein gets built. Simple and strong |
| `shRNAmir (miR-E)` | Same idea, wrapped so the cell handles it through its own machinery. Gentler, and less likely to overload the cell |
| `sgRNA (knockout)` | Cuts the gene itself. **Permanent** — there's no dialling it back |
| `sgRNA (CRISPRi)` | Doesn't cut anything; parks on the gene's on-switch and holds it down |

The program checks your target sequence and will tell you if it's the wrong length, if the
GC content is outside the usual window, or if it has a long run of the same letter (which
causes real problems, including stopping transcription early).

**The most important warning in the program lives here.** Pick `SNCA` and you get this, every
time:

> α-synuclein is required for normal synaptic function. Titrate the dose for partial lowering
> and include a knockdown control: complete nigral loss of α-synuclein has produced
> dopaminergic degeneration in rodent and primate studies.

In plain terms: alpha-synuclein isn't a villain the cell would be better off without. It has a
day job. Removing too much has killed the exact neurons you're trying to save. The goal is
*less*, not *none* — and "how much less" is a hard question that this program can't answer
for you.

### Grippers: where you put them matters

Pick **Intrabody or nanobody** and two more dropdowns appear.

**Localization** decides where the gripper ends up:

- *intracellular* — inside the cell, where Lewy bodies actually form
- *secreted* — sent outside the cell, to catch alpha-synuclein as it spreads from cell to cell
- *ER-retained* — held in the cell's packaging department

**Degradation tag** decides what happens after it grabs something. Add one and the gripper
doesn't just hold alpha-synuclein — it drags it to the cell's shredder. Without one, it holds
on and waits.

Pick *secreted* and a degron together and the program objects: a secretion tag sends the
protein out of the cell, a degron works inside it. The two instructions contradict each other,
so it tells you to pick one.

---

## The parts of the design

The **Expression** section sets everything wrapped around your cargo.

**Promoter** — the on-switch. `hSyn1`, `CaMKIIa` and `TH` only fire in neurons, which is what
you want here. Choose `GfaABC1D` and the program warns you: that one works in astrocytes, the
support cells, not the neurons where Lewy bodies form. Choose a general-purpose one like `CMV`
or `CAG` and it warns that it fires everywhere, including the liver — and that `CMV` in
particular tends to go quiet in neurons after a while.

**Reporter / selection** — an optional glowing marker (`EGFP`, `mCherry`) or a survival gene,
so you can tell which cells took the package. **Linked by** decides how it travels with the
main cargo.

**WPRE**, **polyA**, **bacterial selection** — standard supporting parts. The defaults are
sensible; leave them until you have a reason.

For AAV you also get **Capsid / serotype** (which cells the van can enter), **Delivery route**
(where it's injected), and **self-complementary (scAAV)**, which makes the cargo switch on
faster and more strongly at the cost of **half the space** — about 2,300 letters instead of
4,700. The program recalculates every size check the moment you tick it.

Each capsid and route comes with a note explaining its trade-off. The one to read carefully
is **AAV-PHP.eB**: it crosses from the bloodstream into the brain beautifully *in mice*,
because it uses a mouse protein as its doorway. Humans don't have that protein doing that job.
It's famous, it's everywhere in research papers, and it's one of the most common ways a
gorgeous mouse result turns out to mean nothing for people.

---

## Reading the messages panel

Everything the program has to say appears top right, sorted by how much it matters.

| Mark | Means |
|---|---|
| ✕ | **Blocking.** Something is actually wrong and this design won't work as drawn |
| ! | **Warning.** It'll work, but think about this |
| *(no mark)* | Information. Context about what you picked |

The checks worth knowing about:

- **Size.** Over about 4,700 letters (or 2,300 with scAAV) and nothing packages at all. The
  program blocks it rather than warning, because an oversized design doesn't fail loudly in
  the lab — it quietly packages a cut-off version that looks fine and doesn't work.
- **Reading frame.** If you paste a gene sequence, it checks the length is a multiple of three,
  that it starts with `ATG`, and that there's no premature stop signal hiding inside. A stop
  codon in the middle means the protein gets cut short — an easy mistake, and invisible by eye.
- **Restriction sites.** Lists which lab cutting-enzymes would chop your insert, which tells
  you which ones you can safely use to assemble it.
- **Hidden stop signals in lentivirus.** A particular short sequence inside your cargo can
  truncate the whole vector. It gets flagged.

---

## The map and the parts table

The **circular map** draws your design as a ring, each part a coloured arc sized to scale.
It's the fastest way to see that the cargo is tiny and the supporting parts are not.

The **table** lists every part with its exact position and length. The `Sequence` column is
where the honesty lives:

- *from the sequence box* — you pasted this one in
- *built in* — the program knows this one exactly
- *double-click to paste* — **the program does not have a verified sequence for this part**

That last case is the common one, and it's deliberate. Where the program doesn't have a real
sequence, it writes the letter `N`, meaning "unknown base", repeated to the right length. The
*structure* is real and the *lengths* are typical, but those letters are blank. A
plausible-looking invented sequence would be far more dangerous than an obvious gap, because
you can't spot a wrong one by looking.

To fill one in, double-click the row and paste a verified sequence — from a reference plasmid
on [Addgene](https://www.addgene.org/), for example. The design re-numbers itself around
whatever you paste.

---

## Getting your design out

Four buttons: **Copy GenBank**, **Copy FASTA**, **Save GenBank…**, **Save FASTA…**

**GenBank** is the sequence plus labels for every part. Open a `.gb` file in free software
like SnapGene Viewer or Benchling and you'll see your design laid out and annotated.
**FASTA** is the bare letters, nothing else — what you'd paste into an analysis tool.

The full GenBank file is also shown live at the bottom of the window, so you can watch it
change as you click.

---

## Five minutes to get the idea

1. **Open it and change nothing.** You start on α-synuclein lowering, targeting `SNCA`
   through AAV9 into the putamen. Read the messages — the `SNCA` safety warning is right
   there.
2. **Tick scAAV.** Watch the size limit halve and the messages recalculate.
3. **Switch to lysosomal clearance and pick `GBA1`.** Now tick scAAV. It goes from fine to
   blocked, because a real gene is far bigger than a short lowering cassette. That's the
   packaging squeeze that shapes every decision in this field, in one click.
4. **Switch the promoter to `GfaABC1D`.** Read the warning about targeting the wrong cells.
5. **Go to the intrabody strategy, set localization to secreted and add a degron.** Watch it
   catch the contradiction.

If you only do one, do number 3.

---

## Honest limitations

**The sequences are mostly placeholders.** See the table section above. This designs the
*architecture*; you supply the verified letters.

**The lengths are typical values, not looked-up facts.** Paste a real sequence and the
program uses its real length instead.

**Hitting the target hasn't been enough in this disease.** Treatments aimed at
alpha-synuclein have done exactly what they were designed to do at the molecular level and
still not helped patients in trials — twice, with antibodies. Engaging the target and helping
the person are different achievements, and nothing designed here escapes that record.

**Most of the encouraging animal results come from a setup that flatters them.** The standard
lab model floods neurons with alpha-synuclein to cause damage quickly — which is precisely the
scenario where anything that clears that protein away will look good. Real human disease takes
decades and we don't fully know why it starts.

**This is a design and teaching tool.** It can't make a virus, and it isn't medical advice.

---

## Glossary

| Word | What it means |
|---|---|
| **alpha-synuclein** | The protein that clumps in Parkinson's. Its gene is `SNCA` |
| **Lewy body** | A clump of it inside a brain cell |
| **AAV** | The emptied-out harmless virus used as a delivery van |
| **lentivirus** | A different delivery van that inserts its cargo permanently into the cell's own DNA. Common in lab work, rarer in brain treatments |
| **plasmid** | A loop of DNA used in bacteria and cell culture. No van at all |
| **capsid** | The outer shell of the virus; decides which cells it can enter |
| **promoter** | The on-switch in front of a gene: when and in which cells it's read |
| **payload / cargo / insert** | The gene or gripper being delivered |
| **cassette** | The whole assembly: switches, cargo, labels and ends together |
| **ITR** | The repeats at each end of an AAV cassette. Without them nothing packages |
| **polyA** | The "message ends here" signal after the gene |
| **WPRE** | An extra piece that raises how much protein gets made |
| **bp / kb** | Base pairs — letters of DNA. 1 kb = 1,000 letters. An AAV holds about 4.7 kb |
| **ORF / CDS** | The stretch that actually spells out a protein, start to finish |
| **ATG** | The three letters that mark where a protein starts |
| **stop codon** | Three letters meaning "protein ends here". One in the middle truncates it |
| **GC content** | What fraction of a sequence is G or C. Affects how well things work |
| **reading frame** | DNA is read three letters at a time. Start in the wrong place and every letter after is garbage |
| **shRNA / siRNA** | A short sequence that destroys a gene's message before the protein is built |
| **CRISPR / sgRNA** | A system that finds an exact spot in DNA. With Cas9 it cuts; as CRISPRi it just switches the gene off |
| **nanobody / intrabody / scFv** | Small engineered gripper proteins that latch onto one specific target |
| **degron** | A tag meaning "destroy this" — attached to a gripper, it destroys whatever the gripper caught |
| **epitope** | The exact small patch of a protein a gripper grabs |
| **serotype** | Which variety of AAV, each entering a different set of cells |
| **scAAV** | Self-complementary AAV: switches on faster, holds half as much |
| **restriction site** | A short sequence that a lab cutting-enzyme recognises |
| **GenBank / FASTA** | Two standard DNA file formats. FASTA is bare letters; GenBank adds labels |
| **Addgene** | A non-profit repository where labs share verified plasmid sequences |

---

*Research design tool. Producing virus requires institutional biosafety approval, and clinical
gene therapy products need GMP manufacturing, preclinical safety and efficacy data, and
regulatory authorization. Nothing here is a clinical protocol.*

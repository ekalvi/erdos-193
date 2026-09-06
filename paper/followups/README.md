# Unit-step manuscripts: archive and attribution

**Research checkpoint, September 6, 2026.** These are distinct documents, not
one finished joint paper. The received PDFs are preserved byte-for-byte at
Erik Kalviainen's request. Draft status, a supplier's identity, and final
publication authorship must not be conflated.

## Manuscript chain

| Document | Attribution and contribution | Status / available files |
|---|---|---|
| *An infinite small-step Z³-walk with no collinear triple* (September 1) | **Stijn Cambie and Erik Kalviainen**, the original paper's named authors. Finite-step construction and valuation obstruction in Z³. | Original unconditional theorem, Lean formalization in this repository; [arXiv](https://arxiv.org/abs/2609.01766v1). [PDF](../erdos193.pdf), [LaTeX](../erdos193.tex), [text](../../research/unit-step/text/cambie-kalviainen-original.txt). |
| *An infinite walk in N¹⁶, using only unit steps, with no three collinear points* (September 4) | **Jeffrey Shallit**, named author. Unit-step follow-up, word equivalence, explicit 16-letter substitution, and unproved smaller cyclic candidates, including 5D. Builds on Cambie–Kalviainen. | Received manuscript, not a journal publication. [Unchanged PDF](2026-09-04-shallit-N16.pdf), [text](../../research/unit-step/text/shallit-N16.txt). No LaTeX source supplied in the available material. |
| *A unit-step walk in fourteen dimensions* (September 5) | **Stijn Cambie**, supplier of the note and offset simplification. The PDF itself has no byline. Builds on Cambie–Kalviainen and Shallit; do not rewrite the PDF to invent a byline. | Received note. [Unchanged PDF](2026-09-05-cambie-N14.pdf), [text](../../research/unit-step/text/cambie-N14.txt). Original `unit_step_walk_N14_short.tex` was attached but is **not yet imported**, see below. |
| *A six-dimensional unit-step walk with no collinear triple* (September 5) | **Erik Kalviainen**, named draft author. Alternating signed-Gaussian rule; uses **Cambie's offsets** and **Shallit's basis encoding** on the original Cambie–Kalviainen foundation. | Draft awaiting independent review, not Lean-formalized. [PDF](../unit_step_walk_N6_short.pdf), [LaTeX](../unit_step_walk_N6_short.tex), [text](../../research/unit-step/text/kalviainen-N6.txt), [diagram PDF](../unit_step_g85_g170_context.pdf). Repository PDF is byte-identical to the sent `unit_step_walk_N6_short (1).pdf`; no redundant copy is needed. |
| *A four-letter infinite word avoiding weak abelian cubes* (received September 6) | Supplied by **Jeffrey Shallit**, reported as AI-generated; **no named author appears in the PDF**. Explicitly credits the Cambie–Kalviainen valuation method. Supplier attribution does not assert sole or agreed publication authorship. | Unchecked research draft, preliminary audit only. [Unchanged PDF](2026-09-06-shallit-weak-abelian-cubes.pdf), [text](../../research/unit-step/text/shallit-weak-abelian-cubes.txt), [review notes](../../design/WEAK-ABELIAN-CUBE-DRAFT-REVIEW.md). No LaTeX source supplied in the available material. |

The original proof is [recorded as accepted as correct by the Erdős Problems
site](https://www.erdosproblems.com/forum/thread/193/proof-claims#proof-claim-239)
(checked September 6). This does **not** certify any follow-up manuscript.
The repository's root `CITATION.cff` continues to cite the original two-author
paper; it is not a blanket citation for every archived draft.

## Other PDFs and work in progress

All existing repository PDFs remain available; the archive does not replace or
silently delete older explanatory work:

- [Notation cheat sheet](../notation-cheat-sheet.pdf) and [Markdown source](../notation-cheat-sheet.md).
- [Earlier proof skeleton](../proof-skeleton.pdf) and [Markdown source](../proof-skeleton.md).
- [Six-coordinate context diagram](../unit_step_g85_g170_context.pdf) and
  [renderer](../../design/render_unit_step_context.py).
- [Production copy of the original PDF](../../viz/erdos-193-gaussian-proof.pdf),
  byte-identical to `paper/erdos193.pdf` at this checkpoint.
- [AI checkpoint](../../research/unit-step/AI-CHECKPOINT.md): complete index of
  current unit-step WIP, executable checks, evidence, obstructions, and next tasks.

The older cheat sheet and skeleton are historical aids, not substitutes for
the current Gaussian paper or new proofs of the unit-step follow-up.

## Provenance, AI disclosure, and preservation

The machine-readable [artifact catalogue](../../research/unit-step/artifacts.json)
records each PDF's SHA-256, byte size, page count, source filename/date, attribution,
status, available source, and extracted text. The PDF is authoritative; extracted
text is for AI/search and can lose mathematical formatting. Extraction trims
trailing whitespace and marks undecodable control glyphs with `�` instead of
inventing a mathematical symbol. Consult the PDF at such locations. Reproduction
tools and integrity checks are in [the checkpoint](../../research/unit-step/AI-CHECKPOINT.md).

- Preserve received manuscripts unchanged. Corrections belong in clearly
  attributed review notes or a separately versioned revision, never a silent
  edit of someone else's source document.
- AI assistance is disclosed in the original paper, Shallit's 16D manuscript,
  and Kalviainen's 6D draft. Cambie reported AI assistance for the 14D note;
  Shallit reported the cube draft as generated with “ChatGPT 6 Astra Max” and
  not carefully checked. These are source-reported descriptions, not an
  independent verification of model identities or proof correctness.
- This is a **public GitHub archive authorized by Kalviainen's repository
  request**, not evidence that every contributor has approved a journal text,
  a byline, or a redistribution licence. Attribution is retained; no new
  licence is asserted for third-party manuscripts.
- No private email transcript, mailbox identifier, draft reply, attachment
  access URL, or credential is included.

## Explicit missing-source inventory

| Source | Situation | Safe next action |
|---|---|---|
| Cambie's `unit_step_walk_N14_short.tex` (3,924 bytes) | Present as an attachment, but the Gmail attachment tool rejects MIME `application/x-tex`. The PDF is archived. | Manually download/upload the original `.tex`, then add it with a checksum and provenance. Do not present a reconstructed source as the original. |
| Shallit's 16D LaTeX | No source attachment in the material available for this checkpoint. | Request the source if editable consolidation needs it. |
| Four-letter cube draft LaTeX | No source attachment in the material available for this checkpoint. | Request the source if editable consolidation needs it. |

Thus **all manuscript PDFs in the available correspondence are preserved**;
not all original editable sources have been obtained. Raw runtime checkpoints
and logs remain ignored; the final certificates and reproducible programs are
in Git. The public production website is not changed by this archive.

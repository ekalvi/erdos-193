# Fixed-menu semigroup decision and a failed cardinality descent

**descent-automata track, September 6, 2026. AI-derived arguments and bounded
exact checks; independent review pending, not human approval.** The supplied
`return-blocks.md` is the latest input checkpoint and was not edited.

## 1. Verdict and scope

**The all-finite-menu five-vector subsequence exclusion is not proved here.**
There are three concrete results:

1. **An exact, terminating decision procedure for each specified finite menu.**
   It decides whether the specified `g85` walk has an infinite subsequence with
   that menu, and separately whether one starts at any prescribed index `n0`.
   The existence-somewhere answer is invariant under every phase in the
   primitive substitution subshift. Positive and negative answers both have
   finite, checkable semigroup certificates. This is a theorem about infinity,
   not inference from a surviving prefix.
2. **Automatic-selector extraction.** If any infinite subsequence uses a
   specified finite menu, some base-four automatic selector uses that same
   menu (after a possible initial partial return). Thus arbitrary selectors
   can be reduced to automatic ones, but with no complexity bound here.
3. **An exact obstruction to the proposed cardinality-preserving floor
   descent.** Flooring selected indices by four can turn **five** displacement
   types into **six**, even on a seven-vertex segment. Endpoint corrections
   cannot be dropped or treated as a function of the fine displacement alone.

The procedure is uniform **as an algorithm taking a menu as input**, but its
state count depends on the menu's heights. It does **not** give a finite list
of normalized five-menu states independent of height, nor prove all inputs
of size five are negative. That distinction is the remaining proof gap.

These results concern only Kalviainen's tagged `g85` construction, using
Cambie's offsets and Shallit's basis-encoding principle, on the
Cambie–Kalviainen Gaussian source. They do not change the status of its
triple-avoidance manuscript. No triple-avoidance theorem is used below.
They imply no new bound on `d_*` or `s_*`; even a complete negative answer for
all subsequences of this walk would not prove `s_*=6`. The original Erdős 193
result is separate.

## 2. The exact substitution and height reduction

Use the definitions of the supplied checkpoint:

\[
q_n=\Big[\sum_j(-1)^j b_j(n)\Big]_4,\qquad
z_n=\sum_{t<n}i^{q_t},\qquad
c=(0,-1,-1+i,-i),
\]
\[
Q_n=(\Re(2z_n+c_{q_n}),\Im(2z_n+c_{q_n}),4n+q_n).
\]

Let `t_n=(q_n,q_(n+1))`. In the order

```
a=01, b=12, c=23, d=30, e=02, f=13, g=20, h=31
```

its word `t` is the fixed point starting in `a` of

```
tau(a)=afda   tau(b)=bgab   tau(c)=chbc   tau(d)=decd
tau(e)=afde   tau(f)=bgaf   tau(g)=chbg   tau(h)=dech.
```

This is the established eight-transition substitution, not a new source.
Writing `V` for the displacement coding gives

```
V(a)=( 1, 0,5)  V(b)=( 0, 3,5)  V(c)=(-1,-2,5)  V(d)=(0,-1,1)
V(e)=V(f)=(1,1,6)                 V(g)=V(h)=(-1,-1,2).
```

Every `tau^3(x)` contains all eight letters. Analytically, each image of a
transition with source `r` contains the increment-one transitions with
sources `r,r-1`, and an increment-two transition with source `r+1`.
After two substitutions the increment-one transitions have all four sources;
a further substitution supplies all increment-two transitions. In particular
`tau` is primitive. Its exact adjacent-letter language is

```
ab af bc bg cd ch da de ec fd ga hb.
```

For a finite verification of completeness, start with internal pairs in all
eight images and close under `xy -> last(tau(x)) first(tau(y))`. This gives
exactly the displayed twelve pairs. All internal pairs occur because all
letters occur, and the boundary operation preserves actual occurrence.
Conversely every pair in a substituted word is internal or such a boundary
pair. This proves equality, not presumed stabilization of a prefix.

### A prescribed vector allows at most two gaps

If `v=(X,Y,h)=Q_(n+g)-Q_n` and `g>0`, then

\[
h=4g+s-r,\qquad r=q_n,\ s=q_{n+g}\in\{0,1,2,3\}.
\]

Therefore define

\[
G(h)=\{g\in\mathbb Z_{>0}:\lceil(h-3)/4\rceil\le g
\le\lfloor(h+3)/4\rfloor\}.
\]

It has at most two members. For each source/target pair `(r,s)`, a possible
gap is uniquely fixed by `g=(h-s+r)/4`; also

\[
X+iY=2\sum_{j=0}^{g-1}i^{q_{n+j}}+c_s-c_r.
\]

Thus a specified menu does not require testing every gap up to its largest
one. Only the at most `2|M|` candidate lengths need be considered.
All actual forward displacements have positive height, so vectors of
nonpositive height are discarded. Empty returns are never admitted.

## 3. Complete finite-word encoding of a fixed menu

Let `M` be any finite subset of `Z^3`, after discarding nonpositive heights.
If it is empty, the answer is NO. Otherwise put

\[
H=\max_{v\in M}v_3,\qquad B=\lfloor(H+3)/4\rfloor.
\]

Let `L_M` be the finite language of all nonempty **actual factors** `w` of `t`
with

\[
\sum_{x\text{ in }w}V(x)\in M.
\]

Every such word has length at most `B`, and its length belongs to the
candidate set in Section 2. This language is effectively computable **with
proof of completeness**: choose `k` with `4^k >= B`, expand `tau^k(xy)` for
the twelve adjacent pairs above, and test just the candidate-length factors
of these finite words. A factor of length at most `4^k` meets at most two
aligned substitution blocks; conversely every expanded pair is an actual
factor. Hence this calculation returns exactly `L_M`.

Construct an NFA as follows:

- States are the empty word `epsilon` and every distinct proper prefix of a
  word in `L_M`.
- From prefix `p` on letter `x`, allow the transition to `px` if `px` is a
  proper prefix of a codeword.
- Also allow a transition to `epsilon` if `px` itself is a codeword. Both
  transitions are retained when both conditions hold.

There are no epsilon transitions. A run from `epsilon` records consecutive
menu returns, possibly with an unfinished last return. A non-reset transition
strictly increases the prefix length, which is always less than `B`.
Consequently every infinite run resets infinitely often.

**Exact encoding lemma.** For every `n0`, there is an infinite selected path
starting at `Q_(n0)` using vectors in `M` if and only if this NFA has an
infinite run from `epsilon` on `t_(n0)t_(n0+1)...`.

**Proof.** Each selected edge spells a member of `L_M`, yielding the run.
Conversely the infinitely many resets give strictly increasing indices whose
intervening complete words are in `L_M`, hence whose displacements lie in
`M`. There is no eventual-unfinished-word loophole, by the prefix-length
bound. This transformation preserves the spatial menu: codewords are not
new displacement types; their sums belong to the original `M`. ∎

## 4. Finite semigroup certificates, including phase and start index

Let `r` be the number of NFA states. For each letter `x`, let `A_x` be its
`r` by `r` Boolean transition matrix, with rows as initial states. For a word
`w`, let `A(w)` be the left-to-right Boolean matrix product. Define the tuple

\[
P_k=(P_{k,x})_{x\in\{a,\ldots,h\}},\qquad
P_{k,x}=A(\tau^k(x)).
\]

The exact update is

\[
P_{0,x}=A_x,\qquad
P_{k+1,x}=P_{k,x_1}P_{k,x_2}P_{k,x_3}P_{k,x_4}
\quad\text{if }\tau(x)=x_1x_2x_3x_4.
\]

There are at most `2^(8r^2)` tuples. Detecting a repeated tuple or a zero
component is therefore a terminating finite calculation.

### Theorem A: existence somewhere and arbitrary substitution phase

Let `X_tau` be the one-sided substitution subshift: infinite words all of
whose finite factors occur in `t`. The following are equivalent:

1. Some infinite subsequence of the specified `Q` uses only vectors in `M`.
2. For **every** `w in X_tau`, the displacement walk coded by `w` has such an
   infinite selected tail.
3. No finite factor of `t` has zero transition matrix.
4. Every component of every `P_k`, `k>=0`, is nonzero.
5. The tuple iteration reaches a repeated tuple without encountering any
   zero component.

More precisely, in item 2, for every `w` and every position `N`, some valid
infinite selected path starts at an index in `[N,N+B-1]`.

**Proof.** Primitivity makes every factor of `t` recur arbitrarily late. An
infinite selected path gives an NFA run over an entire tail; a zero-matrix
factor occurring later would be impossible. This proves 1 implies 3.

Every `tau^k(x)` is an actual factor. Conversely every finite factor occurs
in a prefix `tau^k(a)` for sufficiently large `k`. A zero factor makes any
containing word's product zero. Thus 3 and 4 are equivalent.

Under 3, every finite prefix of every `w in X_tau`, or of any suffix of such
`w`, admits an NFA run from some state. There are finitely many states and
finite outdegree, so König's lemma gives an infinite run from some state.
If that state is `epsilon`, the selected path starts immediately. Otherwise
its first reset occurs after at most `B-1` letters, and thereafter the
encoding lemma applies. This proves the strengthened item 2; taking `w=t`
proves 1. Finally, tuple iteration is deterministic in a finite set, proving
4 equivalent to 5. ∎

This covers all ordinary source shifts, all starting base-four residues,
and all words in the substitution hull, not just aligned blocks. It does
**not** assert that a valid selected path starts at every single vertex.

**Negative certificate:** a letter `x` and an exponent `k` with `P_(k,x)=0`.
The recurring block `tau^k(x)` blocks every tail, even when a selected return
crosses either boundary of the block: the matrix includes arbitrary NFA
states at both boundaries.

**Positive certificate:** indices `i<j` with `P_i=P_j` and all components
nonzero through `j`. The update recurrence proves nonvanishing forever;
the theorem gives an infinite path, without claiming it is periodic.
If an input is negative, a zero component is found by exponent at most
`2^(8r^2)`. This very poor bound is finite, not height independent.

### Theorem B: an exactly prescribed start `n0`

Set `W_k=tau^k(a)`. Choose `k0` with `4^k0>n0`, and compute the reachable
row `R_(k0)` from `epsilon` after reading the suffix `W_(k0)[n0:]`.
Because `tau(a)=afda`, update

\[
R_{k+1}=R_k P_{k,f}P_{k,d}P_{k,a},\qquad k\ge k_0.
\]

Iterate the finite pair `(P_k,R_k)`. A zero row gives NO; a repeated pair
with nonzero row gives YES. This decides exactly whether an infinite
`M`-subsequence starts at `Q_(n0)`.

**Proof.** The row formula follows from
`W_(k+1)=W_k tau^k(f) tau^k(d) tau^k(a)`. The rows therefore test exactly
runs from the prescribed start through an increasing family of prefixes
exhausting its entire suffix. Nonzero rows forever are equivalent, by
König's lemma, to an infinite run from `epsilon`. A zero row can never
revive. There are at most `2^(8r^2+r)` pairs, so repetition or extinction
must occur. Apply the encoding lemma. ∎

`n0` is unrestricted, not assumed divisible by four or to be a selected
state of an a priori selector. For an arbitrary hull word without a finite
input description, Theorem A is the phase-uniform assertion; Theorem B's
explicit suffix algorithm is for the specified computable source and its
specified shifts. It does not pretend to decide a prescribed boundary
against an unspecified infinite phase oracle.

### Theorem C: arbitrary selectors reduce to automatic selectors

If an infinite subsequence of the specified `Q` uses a fixed finite menu
`M`, then there is a **4-automatic set of selected indices** giving an
infinite subsequence of this same `Q` using only `M`. The selected path may
start later; this assertion does not prescribe its first index.

**Proof / finite extraction.** Take a positive tuple certificate
`P_i=P_(i+p)`, `p>0`, and put `E_x=P_(i,x)`. Thus

\[
E_x=\prod_{y\text{ in }\tau^p(x)} E_y.
\]

Use the finite decorated alphabet

\[
\mathcal C=\{(x,u,v):E_x[u,v]=1\}.
\]

For every decorated letter choose one chain of intermediate states witnessing
its displayed Boolean product. If `tau^p(x)=y_1...y_L`, this defines a
length-`L=4^p` substitution

\[
\rho(x,u,v)=
(y_1,u,s_1)(y_2,s_1,s_2)\cdots(y_L,s_{L-1},v).
\]

All choices are finite and effective. The first-letter map of `rho` maps
the nonempty set of letters `(a,u,v)` into itself, since `tau^p(a)` begins
with `a`. Choose a cycle of this map of length `c`, and a letter `beta` on
that cycle. Then `rho^c(beta)` begins with `beta`, so `rho^c` has a fixed
point starting there. Its projection to transition letters is precisely
`t`, the fixed point of `tau^(pc)` starting with `a`. Adjacent decorated
letters have matching end/start states: this holds inside each iterated
image by construction and hence throughout the fixed point.

Finally replace each `(x,u,v)` by a chosen actual NFA path from `u` to `v`
on `tau^i(x)`, which exists because `E_x=A(tau^i(x))`. These paths concatenate
to an infinite NFA run on `tau^i(t)=t`. It may start in a nonempty prefix
state; discard the initial partial return up to its first reset. Every
subsequent reset gives a selected vertex and every completed return has
vector in the original `M`.

The decorated fixed point is generated by a uniform substitution of length
`4^(pc)`, and the final expansion has length `4^i`. Reading base-four digits
in groups of `pc`, followed by the `i`-digit within-expansion position, gives
a finite automaton for the run's states and reset bits. Equivalently,
automaticity in a base and in its positive powers coincide, and expansion
by a base power preserves automaticity. Shifting reset positions by one to
obtain vertex indices and modifying a finite prefix also preserve
4-automaticity (finite carry automata suffice). Resets occur infinitely often
with gaps at most `B`. This proves the claim. ∎

This is an exact reduction to **all** automatic selectors, not to the
20-letter phase/transition selector family in the supplied checkpoint.
The automaton, substitution power, and decoration size are unbounded as
`M` varies. No complexity bound depending only on `|M|` is asserted.
The extraction is a mathematical consequence of the tuple certificate;
the bounded checker below tests the tuple method, not a separate
implementation of this decorated-substitution extraction.

## 5. The endpoint corrections, and an exact five-to-six witness

Put `e=(0,1,-1,0)` and `d=(0,1,1+i,1)`. The binary definition gives

\[
q_{4m+a}=[q_m+e_a]_4,\qquad
z_{4m+a}=2z_m+i^{q_m}d_a.
\]

For the second identity, the four Gaussian increments in a block sum to
`2i^(q_m)`, and their successive partial sums are exactly `i^(q_m)d_a`.
Thus the proposed algebraic starting point is correct. For
`D=diag(2,2,4)` and `s=[r+e_a]_4`, the precise correction is

\[
Q_{4m+a}=DQ_m+R(r,a),\qquad
R(r,a)=\big(2i^r d_a+c_s-2c_r,\ 4a+s-4r\big),\quad r=q_m,
\]

where the first entry denotes the two real coordinates. The sixteen
integer triples are:

| `r` | `a=0` | `a=1` | `a=2` | `a=3` |
|---|---|---|---|---|
| 0 | (0,0,0) | (1,0,5) | (2,1,11) | (2,0,12) |
| 1 | (1,0,-3) | (1,3,2) | (0,2,4) | (1,2,9) |
| 2 | (1,-1,-6) | (0,-3,-1) | (-1,-4,1) | (-1,-1,6) |
| 3 | (0,1,-9) | (0,0,-8) | (1,1,-2) | (0,-1,3) |

An edge `4m+a -> 4m'+b` of fine displacement `v` descends to

\[
Q_{m'}-Q_m=D^{-1}\big(v-R(q_{m'},b)+R(q_m,a)\big).
\]

If consecutive parent indices repeat, delete the repeats. Every remaining
parent edge comes from one fine edge crossing between different parent
indices. But its correction depends on **both** endpoint states and phases,
not just `v`. A safe overapproximation takes all 256 endpoint pairs per
fine vector and can have up to `256|M|` vectors; it neither preserves the
five-type budget nor gives a reverse lifting theorem without endpoint
compatibility data.

### Actual cardinality increase at the target budget

Take selected indices and their parents

```
fine:    1, 4,11,14,20,24,32
parent:  0, 1, 2, 3, 5, 6, 8.
```

The actual vertices are

```
fine Q:   (1,0,5), (3,0,17), (4,1,47), (6,1,59),
          (7,5,82), (4,4,96), (8,7,131)
parent Q: (0,0,0), (1,0,5), (2,1,11), (2,0,12),
          (3,3,22), (2,2,24), (4,3,35).
```

Their consecutive vectors are

```
fine:   (2,0,12), (1,1,30), (2,0,12), (1,4,23), (-3,-1,14), (4,3,35)
parent: (1,0,5),  (1,1,6),  (0,-1,1), (1,3,10), (-1,-1,2),  (2,1,11).
```

There are exactly **five** fine types and **six** parent types. Already the
first four selected vertices give a two-to-three increase: the same fine
vector `(2,0,12)` descends once to `(1,0,5)` and once to `(0,-1,1)`.
All indices and coordinates are tiny exact integers; this is not a
counterexample to the infinite five-menu exclusion or the supplied gap-16
result. It refutes the local cardinality lemma a naive descent would need.
An argument using a specially chosen global phase or a different operation
would require a new proof; this witness does not rule out all such variants.

## 6. Bounded exact checks and reproduction

New checker: `research/unit-step/explorations/descent-automata-check.mjs`.
It performs only bounded algebra checks and a handful of fixed-menu
semigroup regressions, not an exhaustive selector/recoding/gap search:

- independently forms `q_n` from binary digits and `Q_n` from Gaussian sums;
- checks the three substitution identities and transition coding through
  index 1024;
- checks primitivity at power 3 and the twelve-pair closure;
- finds the tiny two-to-three witness by testing only three edges, starts
  below 128 and gaps at most 8, specifically to test floor cardinality;
- checks the displayed five-to-six witness directly;
- constructs the exact return language and NFA for the following menus.

| Menu / prescribed start | Exact semigroup outcome |
|---|---|
| Full six-vector menu, any start allowed | YES; `P_0=P_1`, one state |
| Full six-vector menu, prescribed `n0=13` | YES; paired state repeats at levels 2,3 |
| Full menu minus `(0,-1,1)` | NO; the matrix for `d` is already zero |
| Even-state six-vector menu, any start allowed | YES; 13 states, `P_2=P_3` |
| Same even menu, `n0=0` or `n0=3` | YES |
| Same even menu, `n0=1` or `n0=4` | NO; reachable row zero at level 2 |
| Only nonpositive-height vectors | NO |

Here the even menu, independently supplied in the input checkpoint, is

```
(-1,-1,2), (-1,-3,6), (1,1,6), (1,3,10), (-2,0,12), (2,0,12).
```

Its **complete** return language is

```
e f g h ab cd afd bch chb daf fda hbc.
```

This language includes all actual occurrences with these displacement
vectors, not just the returns made by the even-state selector. Its trie has
13 states. The checker emits their order and the eight Boolean matrices
`P_2` (hex bit-mask rows), and checks `P_2=P_3` exactly. The start-dependent
outcomes illustrate why an unrestricted boundary-state certificate must
not be advertised as a path beginning at every prescribed vertex.

Run sequentially from the worktree root:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 UV_THREADPOOL_SIZE=1
mkdir -p .checkpoint-descent-automata
/usr/bin/time -f 'elapsed=%e cpu=%P maxRSS=%MKB' \
  node --single-threaded --max-old-space-size=192 \
  research/unit-step/explorations/descent-automata-check.mjs \
  > .checkpoint-descent-automata/check.json
```

Observed runtime: about **0.1 seconds**, one computational CPU, peak RSS
about **60 MB**; generated JSON below 10 KB. The script has a 10,000-level
regression safety cap and throws an error rather than interpreting the cap
as NO. The theorems above give the terminating unbounded algorithm; this
bounded checker is not an implementation intended for arbitrary enormous
menu inputs. No substantive Python or calculation over 60 seconds was used.

## 7. What remains, strongest next action, and stopping point

For the exact target, the missing assertion can now be written precisely:

> For every finite positive-height `M subset Z^3` with `|M|<=5`, the tuple
> orbit built in Sections 3–4 reaches a zero component.

Every individual input has a finite YES or NO certificate. There is still
an unbounded family of inputs: the trie size and matrix semigroup depend on
menu height. For example, the crude factor-coverage construction bounds the
trie size by `1+192|M|B^2`, not by an absolute constant for five vectors.
Enumerating menus or proving the result for another finite gap cutoff does
not discharge the universal quantifier.

**Strongest next action:** seek an invariant for the *exact* boundary-state
semigroup that forces a zero component when there are at most five completed
return vectors, or prove a height-independent normalization of these
semigroups that retains the original vector-equality classes and boundary
compatibilities. Theorem C makes a second exact formulation available:
exclude all 4-automatic selectors with at most five actual return vectors,
without assuming bounded automaton size. Use the five-to-six witness as a mandatory regression test
for any proposed geometric normalization. Simply replacing each fine vector
by one parent vector is now explicitly disproved.

This report stops at the complete fixed-menu reduction, automatic-selector
extraction, and the failed cardinality descent; no universal negative result
or new construction is claimed. A useful complete report and passing bounded
checks were preserved at the 18-minute checkpoint. No gap-17/32 search, prior exhaustive selector run, large prefix
scan, or rival new output was used. The supplied exploration inputs,
manuscripts, central checkpoints/problem files, and `viz/` were not edited.

### Files changed

Only new outputs:

- `research/unit-step/explorations/descent-automata.md` — this report.
- `research/unit-step/explorations/descent-automata-check.mjs` — bounded exact
  checks and explicit semigroup certificates.

Ignored transient output: `.checkpoint-descent-automata/check.json`.
No commits, network access, package installation, publication, or deployment.

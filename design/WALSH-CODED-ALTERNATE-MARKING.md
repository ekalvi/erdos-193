# A real-world candidate: Walsh-coded Alternate Marking for multipath fault detection

**Status:** concrete application hypothesis with an exact decoder prototype and analytic noise model. It is not an IETF proposal, an RFC-compatible profile, a packet-level benchmark, or a production-readiness claim.

## Verdict

The most credible near-term application of the signed Gaussian family is:

> **Detect persistent severe loss or blackholes across many controlled ECMP, MPLS, or SRv6 paths while using only a constant number of hardware counters at each measurement point.**

The method extends the packet-color idea in IETF Alternate Marking. Instead of instantiating two counters for every monitored flow or path, the ingress assigns each path a signed-Gaussian rule. During a synchronized frame, the path's packets carry one of four marks. A measurement point keeps four aggregate counters, exports one signed sample per slot, and a collector applies a fast Walsh--Hadamard transform to recover every path's volume.

The fit is narrow but real:

- the network is one controlled SDN domain;
- paths or tunnels are stable for one frame;
- measurement-point register/counter state is scarce;
- synchronized slot boundaries are available;
- fixed-rate active probes or nearly constant path volumes are acceptable; and
- the target is a persistent severe fault, not sub-percent loss estimation.

Outside that envelope, conventional per-flow Alternate Marking, direct labeled probes, sketches, or in-band telemetry are likely better.

---

## 1. The operational problem already exists

[RFC 9341](https://www.rfc-editor.org/rfc/rfc9341) standardizes the Alternate-Marking method for loss, delay, and jitter measurements on live traffic. Consecutive traffic blocks receive alternating colors so ingress and egress can read coherent counters.

The RFC identifies the granularity cost directly:

- grouped flows are consistent only when they follow the same path;
- grouping cannot identify which individual flow suffered loss; and
- per-flow measurements require counters configured for every selected flow.

[RFC 8889](https://www.rfc-editor.org/rfc/rfc8889), the experimental multipoint extension, makes the scaling explicit. With $M$ monitored flows and $P$ measurement points, the counter order is

$$
2PM,
$$

one counter per color, flow, and point. It uses network clustering and progressive refinement to control this cost, including ECMP cases.

The signed-family proposal attacks the same counter-state bottleneck from a different direction: **code-division multiplex the path identities into a few aggregate color counters**.

---

## 2. Marking and decoding

Take $N=2^p$ monitored paths and a frame of $N$ slots. Pad with zero-volume paths when the actual path count is smaller.

Assign path $r\in\{0,\ldots,N-1\}$ a $p$-bit rule ID. In slot $n$, mark its packets with

$$
\alpha(r,n)
 =s_2(n)-2\langle r,n\rangle_{\mathbb F_2}\pmod4.
$$

The corresponding signed color is

$$
u_r(n)=i^{\alpha(r,n)}
 =i^{s_2(n)}(-1)^{\langle r,n\rangle}.
$$

The four marks represent $1,i,-1,-i$. If $C_q(n)$ is the aggregate count carrying mark $q$ during slot $n$, form

$$
Y(n)=C_0(n)-C_2(n)+i\bigl(C_1(n)-C_3(n)\bigr).
$$

Suppose path $r$ contributes a constant volume $x_r$ per slot. Then

$$
Y(n)=\sum_r x_r u_r(n).
$$

Remove the common Gaussian phase:

$$
Z(n)=i^{-s_2(n)}Y(n)
     =\sum_r x_r(-1)^{\langle r,n\rangle}.
$$

A Walsh--Hadamard transform recovers every path exactly:

$$
\boxed{
 x_r=\frac1N\sum_{n=0}^{N-1}
 Z(n)(-1)^{\langle r,n\rangle}.
}
$$

Run the decoder on both ingress and egress counters. Their difference gives each path's loss under the constant-volume model. Multiple measurement points can localize the segment where the decoded volume decreases.

### Hardware simplification

The Gaussian phase is common to every path and known from the slot number. A minimal implementation can transmit only the Walsh sign bit and derive the phase at the collector. That reduces the data-plane state to two aggregate counters rather than four. The four-color form is retained here because it is the direct signed-Gaussian representation and fits a two-bit marking field.

This would be a new controlled-domain marking profile; reusing one or two bits does not make it semantically compatible with RFC 9341.

### Does one family shape work best?

No—not in the synchronized constant-rate model. The measurement uses the complete set of increment sequences, not the shapes of their cumulative planar walks. For any rules $r$ and $s$,

$$
\sum_{n=0}^{N-1}u_r(n)\overline{u_s(n)}=N\,\delta_{rs}.
$$

Every rule therefore has the same energy, matched-filter gain, and independent-loss variance. Relabeling rules only permutes the decoded paths, and any subset of distinct rows remains orthogonal. In particular, the family member that has the best geometric triangle conditioning for mobile-anchor localization has no corresponding advantage here.

Rule choice can matter only after the ideal assumptions fail. Bursty path volumes leak according to the Walsh spectrum indexed by $r\oplus s$, so an assignment could be optimized from measured traffic traces, but there is no traffic-independent best rule. Clock offsets also distinguish rows, but even favorable rows produce false coefficients; synchronization and guard handling are the remedy, not visual shape selection.

The practical choices are instead to use the smallest power-of-two frame that covers the active paths, omit the common Gaussian phase when a two-color implementation is possible, assign the complete codebook by a stable path-ID mapping, and use cluster-then-refine frames when a single full frame becomes too large.

---

## 3. Why this is implementable

### Ingress

For each stable path, tunnel, or policy, store a short rule ID. A synchronized slot counter supplies $n$. The mark is

```text
alpha = (popcount(slot_id) - 2 * parity(rule_id & slot_id)) mod 4
```

Only the low $p$ bits enter one frame. Bit ordering merely permutes rule IDs.

A programmable switch could implement fixed-width parity with XOR stages or a small table. This still requires one path-to-rule assignment entry at ingress, but intermediate measurement points no longer require per-path counters.

### Measurement point

Maintain four monotone counters, one for each mark. At each slot boundary, snapshot counter deltas. Since the common phase identifies the active opposite pair, a capable data plane can export one signed difference per slot; otherwise it exports four deltas.

### Collector

For each frame:

1. align samples to slot IDs;
2. compute $Y(n)$ from color deltas;
3. multiply by $i^{-s_2(n)}$;
4. run an $O(N\log N)$ fast Walsh--Hadamard transform; and
5. compare decoded ingress and egress volumes.

For $N=256$, this is negligible controller work.

---

## 4. Prototype

Run the bounded expected-value model:

```bash
python3 design/coded_alternate_marking.py
```

A larger hard-failure scenario is:

```bash
python3 design/coded_alternate_marking.py \
  --paths 256 --slot-ms 1 --impaired-path 193 --impaired-delivery 0
```

The implementation uses exact rational arithmetic for the constant-rate decoder. It also reports the analytic Bernoulli-loss variance and deliberately decodes with a one-slot clock error to expose synchronization sensitivity.

### Scenario A: 64 paths, one path delivers 90%

Parameters: one active probe per path per 10-ms slot, normal delivery 99.9%, 64 slots per frame.

| Measure | Result |
|---|---:|
| frame duration | 640 ms |
| probe packets per frame | 4,096 |
| conventional two-color per-path counters / point | 128 |
| signed-family aggregate counters / point | 4 |
| counter-state reduction | 32x |
| exact expected-volume decoder error | 0 |
| one-frame coded delivery standard error | 4.89 percentage points |
| independent frames for a five-sigma 9.9-point gap | 7 |
| approximate detection time | 4.48 s |

Dedicated per-path counters have a 3.75-point standard error on the impaired path in the same probe model. Coding is less precise because every decoded coefficient contains packet-delivery noise from every path.

### Scenario B: 256 paths, one persistent blackhole

Parameters: one probe per path per 1-ms slot, normal delivery 99.9%, 256 slots.

| Measure | Result |
|---|---:|
| frame duration | 256 ms |
| probe packets per frame | 65,536 |
| conventional two-color per-path counters / point | 512 |
| signed-family aggregate counters / point | 4 |
| counter-state reduction | 128x |
| independent frames for a five-sigma blackhole gap | 1 |

At 64 bytes per probe and ignoring framing overhead, that active load is about 131 Mbit/s. It is small relative to a 100-Gbit/s fabric but not free. Hierarchical probing should reduce it before deployment.

### Clock synchronization failure

In Scenario A, cyclically assigning all samples to a slot one position late produces a root-mean-square coefficient error of approximately 1.41 for a nominal coefficient near 1. This is catastrophic, not graceful degradation. Frame delimiters, guard intervals, and shared clock validation are mandatory.

---

## 5. Noise and traffic variation

### 5.1 Independent packet loss

Let every path send $K$ probes per slot and let path $s$ deliver each independently with probability $q_s$. The decoded estimator is unbiased, but

$$
\operatorname{Var}(\widehat q_r)
 =\frac{1}{NK}\sum_s q_s(1-q_s).
$$

A dedicated per-path counter instead has

$$
\operatorname{Var}(\widehat q_r^{\mathrm{direct}})
 =\frac{q_r(1-q_r)}{NK}.
$$

The coded method has a **multiplex disadvantage under packet shot noise**: other paths' randomness enters every estimate. It is attractive when hardware state dominates and faults are large and persistent, not when statistical precision dominates.

### 5.2 Variable passive traffic

If path volume is $x_s(n)$ rather than a constant, decoding path $r$ returns

$$
\widehat x_r
 =\frac1N\sum_n x_r(n)
 +\sum_{s\ne r}\frac1N\sum_n
 x_s(n)(-1)^{\langle r\oplus s,n\rangle}.
$$

The second term is Walsh-spectral leakage from every other path's variation. Bursty production traffic can therefore look like loss or another path's volume.

The first prototype should use shaped active probes. Passive deployment should proceed only if real traces show leakage below an explicit error budget.

### 5.3 Rerouting

A rule identifies a path only while the path assignment is stable. ECMP rehashing or SR-policy changes within a frame mix coefficients. The controller must either terminate the frame on route change or encode stable tunnel/policy identities rather than unconstrained five-tuples.

---

## 6. Where the infinite-walk theorem enters—and where it does not

The operational decoder uses the family's Walsh identity. It does **not** need the no-three-collinear theorem. This is important: ordinary Walsh codes can implement the same synchronous measurement system.

The signed Gaussian construction contributes:

- the discovery and compact generation of the full rule family;
- a common four-phase scrambling sequence;
- a nested family in which one more sign bit becomes relevant whenever the frame doubles; and
- a tagged cumulative trajectory with an all-interval anti-rate-repetition certificate.

The last item could serve as a one-sided schedule-integrity check: a correctly generated tagged mark/time stream cannot produce three collinear cumulative snapshots. Observing such a triple proves that the expected scheduler trace was not followed. Absence of a collinear triple does not prove correctness, so this is not yet a compelling deployment feature.

The honest claim is therefore:

> this is a real application of the signed **family's code structure**, not yet a real application whose performance depends on the Erdős no-collinearity conclusion.

### A deployed analogue already exists

The factorization into a Walsh row and a common complex phase is structurally the same channelization-plus-scrambling architecture used by WCDMA: Orthogonal Variable Spreading Factor codes supply Walsh/Hadamard channel separation, followed by a scrambling sequence. This confirms that the code family is hardware-realistic, but it also removes any novelty claim based on orthogonality alone. For representative OVSF engineering literature, see C.-M. Chao, Y.-C. Tseng, and L.-C. Wang, *Reducing internal and external fragmentations of OVSF codes in WCDMA systems with multiple codes*, IEEE Trans. Wireless Commun. 4 (2005), [doi:10.1109/TWC.2005.850332](https://doi.org/10.1109/TWC.2005.850332).

---

## 7. Best deployment niche

A plausible first target is a provider or data-center controlled domain with 64--256 stable SRv6 policies, MPLS tunnels, or pinned ECMP test flows crossing a shared measurement point.

Use the scheme when:

- the switch can classify paths at ingress but lacks hundreds or thousands of independent counter registers at every interior point;
- exporting one synchronized sample per millisecond or tens of milliseconds is acceptable;
- the operator wants fast localization of blackholes or losses on the order of 10%, not billing-grade loss ratios; and
- PTP-quality timing or an equivalent frame protocol is already present.

Do not use it when:

- the collector receives individually labeled probes anyway;
- normal packet headers expose a key suitable for a conventional sketch;
- traffic is highly bursty and cannot be shaped;
- paths change within a frame;
- measurement points cannot snapshot counters at slot boundaries; or
- sub-percent precision is required.

---

## 8. Comparison with alternatives

| Method | Counter state | Synchronization | Variable traffic | Per-path precision |
|---|---:|---:|---:|---:|
| RFC 9341 per-flow counters | $2M$ / point | marking-period alignment | strong | strong |
| RFC 8889 clustering | depends on active granularity | marking-period alignment | strong within monitored flow | refined on demand |
| labeled active probes | little switch state | modest | unaffected | strong if collector sees IDs |
| hash/sketch telemetry | fixed configurable memory | usually none | strong | approximate |
| in-band telemetry | state carried in packets | none to modest | strong | high, with header cost |
| signed-family coding | 2 or 4 / point | **strict frame alignment** | weak unless probes are shaped | best for severe persistent faults |

The proposed method earns a trial only where constant counter state is more valuable than synchronization, probe, and decoding costs.

---

## 9. Next engineering gate

Build a P4/BMv2 or equivalent software-switch prototype with 64 pinned paths:

1. ingress table maps a path label to a 6-bit rule ID;
2. a controller distributes slot and frame boundaries;
3. packets receive a two-bit mark;
4. ingress, midpoint, and egress expose four aggregate counters;
5. the collector performs the transform and reports path loss;
6. Linux traffic control injects 0%, 1%, 10%, and 100% path loss; and
7. clock offsets of 0, 0.1, 0.5, and 1 slot test robustness.

Compare against per-flow Alternate Marking and a Count-Min-style counter sketch at equal register memory and equal exported bytes.

### Go/no-go thresholds

Proceed beyond a lab prototype only if all hold:

- 100% blackholes are identified within one frame with no false path identification;
- 10% persistent loss is identified within five seconds at 64 paths;
- a 0.1-slot timing error does not create a false severe-fault alarm after guard handling;
- register state falls by at least 16x at equal measurement points;
- exported telemetry remains below 1% of monitored traffic; and
- the method beats a standard sketch at the same switch-memory budget on the chosen severe-fault workload.

If these fail, the real-world conclusion should remain the established one: the family is a Walsh/OVSF-style synchronous codebook, already useful in communications but not a competitive new network telemetry mechanism.

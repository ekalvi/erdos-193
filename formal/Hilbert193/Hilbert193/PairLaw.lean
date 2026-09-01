import Hilbert193.Transducer
import Hilbert193.Valuation

namespace Hilbert193

open Orient

/-- Numeric value of one base-4 digit. -/
def Digit.toNat : Digit → ℕ
  | .d0 => 0 | .d1 => 1 | .d2 => 2 | .d3 => 3

/-- Evaluate a least-significant-digit-first base-4 word. -/
def indexLSB : List Digit → ℕ
  | [] => 0
  | d :: ds => d.toNat + 4 * indexLSB ds

/-- Reverse one transition, starting from its outgoing orientation. -/
def previous (out : Orient) (d : Digit) : Orient := out.compose (refinement d)

/-- Coordinate bits read from low to high, starting at the common terminal orientation. -/
def coordinateLSB : Orient → List Digit → ℕ × ℕ
  | _, [] => (0, 0)
  | out, d :: ds =>
      let b := emit out d
      let q := coordinateLSB (previous out d) ds
      (b.1.toNat + 2*q.1, b.2.toNat + 2*q.2)

abbrev intDelta (a b : ℕ) : ℤ := (a : ℤ) - (b : ℤ)

def coordinateDelta (out : Orient) (a b : List Digit) : Vec2 :=
  let x := coordinateLSB out a
  let y := coordinateLSB out b
  (intDelta x.1 y.1, intDelta x.2 y.2)

def indexDistance (a b : List Digit) : ℕ :=
  Int.natAbs (intDelta (indexLSB a) (indexLSB b))

@[simp] theorem previous_refinement (out : Orient) (d : Digit) :
    next (previous out d) d = out := by
  simp [previous, next, Orient.compose_assoc]

/-- Different digits emit different bit pairs in every outgoing orientation. -/
theorem emit_injective_out (out : Orient) {d e : Digit} (h : emit out d = emit out e) : d = e := by
  rcases out with ⟨s,x,y⟩
  cases s <;> cases x <;> cases y <;> cases d <;> cases e <;>
    simp_all [emit, child, Orient.act, Orient.choose]

private theorem bit_low_unique (a b : Bit) (x y : ℕ)
    (h : a.toNat + 2*x = b.toNat + 2*y) : a = b := by
  cases a <;> cases b <;> simp [Bit.toNat] at h ⊢ <;> omega

/-- Fixed-terminal low-end coordinates are injective on words of one length. -/
theorem coordinateLSB_injective (out : Orient) {a b : List Digit}
    (hlen : a.length = b.length) (hcoord : coordinateLSB out a = coordinateLSB out b) : a = b := by
  induction a generalizing out b with
  | nil =>
      cases b <;> simp_all
  | cons d ds ih =>
      cases b with
      | nil => simp at hlen
      | cons e es =>
          simp only [coordinateLSB] at hcoord
          have hx := congrArg Prod.fst hcoord
          have hy := congrArg Prod.snd hcoord
          simp only at hx hy
          have hbits : emit out d = emit out e := by
            apply Prod.ext
            · exact bit_low_unique _ _ _ _ hx
            · exact bit_low_unique _ _ _ _ hy
          have hde : d = e := emit_injective_out out hbits
          subst e
          have htail : coordinateLSB (previous out d) ds = coordinateLSB (previous out d) es := by
            apply Prod.ext
            · exact Nat.mul_left_cancel (by omega) (Nat.add_left_cancel hx)
            · exact Nat.mul_left_cancel (by omega) (Nat.add_left_cancel hy)
          have hlen' : ds.length = es.length := by simpa using hlen
          rw [ih (previous out d) hlen' htail]

private theorem padicValNat_eq_zero_of_odd {n : ℕ} (hodd : n % 2 = 1) :
    padicValNat 2 n = 0 := by
  apply padicValNat.eq_zero_of_not_dvd
  intro hd
  obtain ⟨k, rfl⟩ := hd
  omega

private theorem padicValNat_eq_one_of_mod_four_two {n : ℕ} (hmod : n % 4 = 2) :
    padicValNat 2 n = 1 := by
  have hn : n ≠ 0 := by omega
  have htwo : 2 ∣ n := by omega
  obtain ⟨q, rfl⟩ := htwo
  have hqodd : q % 2 = 1 := by omega
  rw [padicValNat.mul]
  · rw [padicValNat_base (by omega), padicValNat_eq_zero_of_odd hqodd]
  · omega
  · omega

private theorem indexDistance_head_mod (d e : Digit) (ds es : List Digit) :
    d ≠ e →
    (d.toNat + 4 * indexLSB ds) ≠ (e.toNat + 4 * indexLSB es) := by
  intro hde heq
  have hm : d.toNat % 4 = e.toNat % 4 := by omega
  cases d <;> cases e <;> simp [Digit.toNat] at hde hm

private theorem indexLSB_injective {a b : List Digit}
    (hlen : a.length = b.length) (hindex : indexLSB a = indexLSB b) : a = b := by
  induction a generalizing b with
  | nil =>
      cases b <;> simp_all
  | cons d ds ih =>
      cases b with
      | nil => simp at hlen
      | cons e es =>
          simp only [indexLSB] at hindex
          have hmod : d.toNat % 4 = e.toNat % 4 := by omega
          have hde : d = e := by
            cases d <;> cases e <;> simp_all [Digit.toNat]
          subst e
          have htail : indexLSB ds = indexLSB es := by omega
          have hlen' : ds.length = es.length := by simpa using hlen
          rw [ih hlen' htail]

private def bitDelta (a b : Bit) (x y : ℕ) : ℤ :=
  intDelta (a.toNat + 2*x) (b.toNat + 2*y)

private theorem bitDelta_ne_zero_of_ne {a b : Bit} (x y : ℕ) (hab : a ≠ b) :
    bitDelta a b x y ≠ 0 := by
  cases a <;> cases b <;> simp_all [bitDelta, intDelta, Bit.toNat]
  all_goals omega

private theorem coordVal_bitDelta_of_ne {a b : Bit} (x y : ℕ) (hab : a ≠ b) :
    coordVal (bitDelta a b x y) = 0 := by
  unfold coordVal
  apply padicValNat.eq_zero_of_not_dvd
  intro hd
  have hdI : (2 : ℤ) ∣ bitDelta a b x y := by
    apply Int.dvd_natAbs.mp
    exact Int.natCast_dvd_natCast.mpr hd
  obtain ⟨k, hk⟩ := hdI
  cases a <;> cases b <;> simp_all [bitDelta, intDelta, Bit.toNat]
  all_goals omega

private theorem coordVal_bitDelta_ne_zero_of_eq {a b : Bit} (x y : ℕ)
    (hab : a = b) (hz : bitDelta a b x y ≠ 0) :
    coordVal (bitDelta a b x y) ≠ 0 := by
  subst b
  unfold coordVal
  intro hv
  rw [padicValNat.eq_zero_iff] at hv
  rcases hv with hbad | hzero | hnotdvd
  · omega
  · exact hz (Int.natAbs_eq_zero.mp hzero)
  · apply hnotdvd
    have hdI : (2 : ℤ) ∣ bitDelta a a x y := by
      refine ⟨(x : ℤ) - y, ?_⟩
      cases a <;> simp [bitDelta, intDelta, Bit.toNat] <;> ring
    apply Int.natCast_dvd_natCast.mp
    exact Int.dvd_natAbs.mpr hdI

private theorem pairVal_bitDelta (a₁ a₂ b₁ b₂ : Bit) (x₁ x₂ y₁ y₂ : ℕ)
    (hmismatch : a₁ ≠ b₁ ∨ a₂ ≠ b₂) :
    pairVal (bitDelta a₁ b₁ x₁ y₁, bitDelta a₂ b₂ x₂ y₂) =
      if a₁ ≠ b₁ ∧ a₂ ≠ b₂ then 1 else 0 := by
  by_cases h₁ : a₁ = b₁ <;> by_cases h₂ : a₂ = b₂
  · exfalso
    exact hmismatch.elim (fun hn => hn h₁) (fun hn => hn h₂)
  · subst b₁
    have hz₂ := bitDelta_ne_zero_of_ne x₂ y₂ h₂
    have hv₂ := coordVal_bitDelta_of_ne x₂ y₂ h₂
    by_cases hz₁ : bitDelta a₁ a₁ x₁ y₁ = 0
    · simp [h₂, pairVal, hz₁, hz₂, hv₂]
    · have hv₁ := coordVal_bitDelta_ne_zero_of_eq x₁ y₁ rfl hz₁
      simp [h₂, pairVal, hz₁, hz₂, hv₁, hv₂]
  · subst b₂
    have hz₁ := bitDelta_ne_zero_of_ne x₁ y₁ h₁
    have hv₁ := coordVal_bitDelta_of_ne x₁ y₁ h₁
    by_cases hz₂ : bitDelta a₂ a₂ x₂ y₂ = 0
    · simp [h₁, pairVal, hz₁, hz₂, hv₁]
    · have hv₂ := coordVal_bitDelta_ne_zero_of_eq x₂ y₂ rfl hz₂
      simp [h₁, pairVal, hz₁, hz₂, hv₁, hv₂, Ne.symm hv₂]
  · have hz₁ := bitDelta_ne_zero_of_ne x₁ y₁ h₁
    have hz₂ := bitDelta_ne_zero_of_ne x₂ y₂ h₂
    have hv₁ := coordVal_bitDelta_of_ne x₁ y₁ h₁
    have hv₂ := coordVal_bitDelta_of_ne x₂ y₂ h₂
    simp [h₁, h₂, pairVal, hz₁, hz₂, hv₁, hv₂]

theorem padicValNat_natAbs_eq_zero {z : ℤ} (hodd : ¬(2 : ℤ) ∣ z) :
    padicValNat 2 z.natAbs = 0 := by
  apply padicValNat.eq_zero_of_not_dvd
  intro hd
  apply hodd
  apply Int.dvd_natAbs.mp
  exact Int.natCast_dvd_natCast.mpr hd

theorem padicValNat_natAbs_eq_one {z : ℤ}
    (htwo : (2 : ℤ) ∣ z) (hfour : ¬(4 : ℤ) ∣ z) :
    padicValNat 2 z.natAbs = 1 := by
  have htwoN : 2 ∣ z.natAbs := by
    apply Int.natCast_dvd_natCast.mp
    exact Int.dvd_natAbs.mpr htwo
  obtain ⟨q, hq⟩ := htwoN
  have hq0 : q ≠ 0 := by
    intro h
    subst q
    simp_all
  have hqodd : ¬2 ∣ q := by
    intro h
    apply hfour
    apply Int.dvd_natAbs.mp
    apply Int.natCast_dvd_natCast.mpr
    simpa [hq, mul_assoc] using Nat.mul_dvd_mul_left 2 h
  rw [hq, padicValNat.mul (by omega) hq0, padicValNat_base (by omega)]
  simp [padicValNat.eq_zero_of_not_dvd hqodd]

private theorem index_mismatch_val (d e : Digit) (ds es : List Digit) (hde : d ≠ e) :
    padicValNat 2 (indexDistance (d :: ds) (e :: es)) =
      if d.toNat % 2 = e.toNat % 2 then 1 else 0 := by
  by_cases hp : d.toNat % 2 = e.toNat % 2
  · rw [if_pos hp]
    apply padicValNat_natAbs_eq_one
    · unfold intDelta indexLSB
      cases d <;> cases e <;> simp [Digit.toNat] at hde hp ⊢ <;> omega
    · unfold intDelta indexLSB
      cases d <;> cases e <;> simp [Digit.toNat] at hde hp ⊢
      all_goals
        rintro ⟨k, hk⟩
        omega
  · rw [if_neg hp]
    apply padicValNat_natAbs_eq_zero
    unfold intDelta indexLSB
    cases d <;> cases e <;> simp [Digit.toNat] at hde hp ⊢ <;> omega

/-- At the first low digit mismatch, both sides of the pair law are 0 or 1
according to whether the two base-4 digits differ in one or two Gray bits. -/
theorem first_mismatch_pairVal (out : Orient) (d e : Digit) (ds es : List Digit)
    (hde : d ≠ e) :
    pairVal (coordinateDelta out (d :: ds) (e :: es)) =
      padicValNat 2 (indexDistance (d :: ds) (e :: es)) := by
  have hm : emit out d ≠ emit out e := fun h => hde (emit_injective_out out h)
  rw [index_mismatch_val d e ds es hde]
  simp only [coordinateDelta, coordinateLSB]
  rw [show
    (intDelta ((emit out d).1.toNat + 2 * (coordinateLSB (previous out d) ds).1)
        ((emit out e).1.toNat + 2 * (coordinateLSB (previous out e) es).1),
      intDelta ((emit out d).2.toNat + 2 * (coordinateLSB (previous out d) ds).2)
        ((emit out e).2.toNat + 2 * (coordinateLSB (previous out e) es).2)) =
    (bitDelta (emit out d).1 (emit out e).1
        (coordinateLSB (previous out d) ds).1 (coordinateLSB (previous out e) es).1,
      bitDelta (emit out d).2 (emit out e).2
        (coordinateLSB (previous out d) ds).2 (coordinateLSB (previous out e) es).2) by
      rfl]
  rw [pairVal_bitDelta _ _ _ _ _ _ _ _ (by
    by_contra h
    push_neg at h
    exact hm (Prod.ext h.1 h.2))]
  rcases out with ⟨s,x,y⟩
  cases s <;> cases x <;> cases y <;> cases d <;> cases e <;>
    simp_all [Digit.toNat, emit, child, Orient.act, Orient.choose]

/-- The exact same-terminal low-end pair law for equal-length words. -/
theorem pair_law_words (out : Orient) {a b : List Digit}
    (hlen : a.length = b.length) (hne : a ≠ b) :
    pairVal (coordinateDelta out a b) = padicValNat 2 (indexDistance a b) := by
  induction a generalizing out b with
  | nil =>
      cases b <;> simp_all
  | cons d ds ih =>
      cases b with
      | nil => simp at hlen
      | cons e es =>
          by_cases hde : d = e
          · subst e
            have hlen' : ds.length = es.length := by simpa using hlen
            have hne' : ds ≠ es := by simpa using hne
            have htail := ih (previous out d) hlen' hne'
            have hcoord : coordinateDelta out (d :: ds) (d :: es) =
                ((2 : ℤ) * (coordinateDelta (previous out d) ds es).1,
                 (2 : ℤ) * (coordinateDelta (previous out d) ds es).2) := by
              simp [coordinateDelta, coordinateLSB, intDelta]
              constructor <;> ring
            have hindex : indexDistance (d :: ds) (d :: es) =
                4 * indexDistance ds es := by
              unfold indexDistance intDelta
              change
                Int.natAbs
                    (((d.toNat + 4 * indexLSB ds : ℕ) : ℤ) -
                      ((d.toNat + 4 * indexLSB es : ℕ) : ℤ)) =
                  4 * Int.natAbs ((indexLSB ds : ℤ) - indexLSB es)
              rw [show
                ((d.toNat + 4 * indexLSB ds : ℕ) : ℤ) -
                    ((d.toNat + 4 * indexLSB es : ℕ) : ℤ) =
                  (4 : ℤ) * ((indexLSB ds : ℤ) - indexLSB es) by
                    push_cast
                    ring]
              rw [Int.natAbs_mul]
              norm_num
            have htail_ne : coordinateDelta (previous out d) ds es ≠ (0,0) := by
              intro hz
              have hx := congrArg Prod.fst hz
              have hy := congrArg Prod.snd hz
              simp [coordinateDelta, intDelta] at hx hy
              have hc : coordinateLSB (previous out d) ds =
                  coordinateLSB (previous out d) es := by
                apply Prod.ext <;> omega
              exact hne' (coordinateLSB_injective _ hlen' hc)
            have hdist : indexDistance ds es ≠ 0 := by
              intro hz
              unfold indexDistance intDelta at hz
              have hiZ : (indexLSB ds : ℤ) = indexLSB es := by
                apply Int.sub_eq_zero.mp
                exact Int.natAbs_eq_zero.mp hz
              have hi : indexLSB ds = indexLSB es := by exact_mod_cast hiZ
              exact hne' (indexLSB_injective hlen' hi)
            have hscale :
                pairVal ((2 : ℤ) * (coordinateDelta (previous out d) ds es).1,
                  (2 : ℤ) * (coordinateDelta (previous out d) ds es).2) =
                pairVal (coordinateDelta (previous out d) ds es) +
                  2 * padicValNat 2 2 := by
              simpa using pairVal_nsmul 2 _ (by omega) htail_ne
            rw [hcoord, hscale, hindex, padicValNat.mul (by omega) hdist]
            have hval2 : padicValNat 2 2 = 1 := padicValNat_base (by omega)
            have hval4 : padicValNat 2 4 = 2 := by
              rw [show 4 = 2 * 2 by norm_num, padicValNat.mul (by omega) (by omega), hval2]
            rw [hval4, hval2, htail]
            omega
          · exact first_mismatch_pairVal out d e ds es hde

/-- Orientation reached while undoing low digits from a fixed outgoing state. -/
def backwardState : Orient → List Digit → Orient
  | out, [] => out
  | out, d :: ds => backwardState (previous out d) ds

@[simp] theorem backwardState_append (out : Orient) (a b : List Digit) :
    backwardState out (a ++ b) = backwardState (backwardState out a) b := by
  induction a generalizing out with
  | nil => rfl
  | cons d ds ih => simp [backwardState, ih]

theorem backwardState_run_reverse (s : Orient) (ds : List Digit) :
    backwardState (run s ds).2 ds.reverse = s := by
  induction ds generalizing s with
  | nil => rfl
  | cons d ds ih =>
      rw [show (run s (d :: ds)).2 = (run (next s d) ds).2 by rfl,
        List.reverse_cons, backwardState_append, ih]
      simp [backwardState, previous, next, Orient.compose_assoc,
        refinement_involution, Orient.compose_I_right]

theorem coordinateLSB_append (out : Orient) (a b : List Digit) :
    coordinateLSB out (a ++ b) =
      ((coordinateLSB out a).1 +
          2 ^ a.length * (coordinateLSB (backwardState out a) b).1,
        (coordinateLSB out a).2 +
          2 ^ a.length * (coordinateLSB (backwardState out a) b).2) := by
  induction a generalizing out with
  | nil => simp [coordinateLSB, backwardState]
  | cons d ds ih =>
      simp only [List.cons_append, coordinateLSB, backwardState, List.length_cons,
        Nat.pow_succ]
      rw [ih]
      apply Prod.ext <;> simp <;> ring

/-- Any number of high zero digit-pairs. -/
def zeroPairs : ℕ → List Digit
  | 0 => []
  | k + 1 => .d0 :: .d0 :: zeroPairs k

@[simp] theorem zeroPairs_length (k : ℕ) : (zeroPairs k).length = 2 * k := by
  induction k with
  | zero => rfl
  | succ k ih => simp [zeroPairs, ih]; omega

@[simp] theorem indexLSB_zeroPairs (k : ℕ) : indexLSB (zeroPairs k) = 0 := by
  induction k with
  | zero => rfl
  | succ k ih => simp [zeroPairs, indexLSB, Digit.toNat, ih]

@[simp] theorem coordinateLSB_I_zeroPairs (k : ℕ) :
    coordinateLSB I (zeroPairs k) = (0,0) := by
  induction k with
  | zero => rfl
  | succ k ih =>
      have hSS : S.compose S = I := by decide
      simp [zeroPairs, coordinateLSB, previous, emit, child, Orient.act,
        Orient.choose, refinement, Digit.toNat, Bit.toNat, hSS, ih]

@[simp] theorem backwardState_I_zeroPairs (k : ℕ) :
    backwardState I (zeroPairs k) = I := by
  induction k with
  | zero => rfl
  | succ k ih =>
      have hSS : S.compose S = I := by decide
      simp [zeroPairs, backwardState, previous, refinement, hSS, ih]

theorem indexLSB_append_zeroPairs (a : List Digit) (k : ℕ) :
    indexLSB (a ++ zeroPairs k) = indexLSB a := by
  induction a with
  | nil => simp [indexLSB]
  | cons d ds ih => simp [indexLSB, ih]

theorem coordinateLSB_append_zeroPairs (out : Orient) (a : List Digit) (k : ℕ)
    (hback : backwardState out a = I) :
    coordinateLSB out (a ++ zeroPairs k) = coordinateLSB out a := by
  rw [coordinateLSB_append, hback, coordinateLSB_I_zeroPairs]
  simp

/-- The pair law remains valid for unequal even word lengths once both words
undo from one common terminal orientation; high zero-pairs provide a common
length. -/
theorem pair_law_even_words (out : Orient) {a b : List Digit}
    (haeven : Even a.length) (hbeven : Even b.length)
    (haback : backwardState out a = I) (hbback : backwardState out b = I)
    (hindex : indexLSB a ≠ indexLSB b) :
    pairVal (coordinateDelta out a b) = padicValNat 2 (indexDistance a b) := by
  obtain ⟨la, hla⟩ := haeven
  obtain ⟨lb, hlb⟩ := hbeven
  let ap := a ++ zeroPairs lb
  let bp := b ++ zeroPairs la
  have hlen : ap.length = bp.length := by
    simp [ap, bp, hla, hlb]
    omega
  have hcoordA : coordinateLSB out ap = coordinateLSB out a :=
    coordinateLSB_append_zeroPairs out a lb haback
  have hcoordB : coordinateLSB out bp = coordinateLSB out b :=
    coordinateLSB_append_zeroPairs out b la hbback
  have hindexA : indexLSB ap = indexLSB a := indexLSB_append_zeroPairs a lb
  have hindexB : indexLSB bp = indexLSB b := indexLSB_append_zeroPairs b la
  have hne : ap ≠ bp := by
    intro h
    apply hindex
    rw [← hindexA, ← hindexB, h]
  have hp := pair_law_words out hlen hne
  simpa [coordinateDelta, indexDistance, hcoordA, hcoordB, hindexA, hindexB] using hp

theorem coordinateLSB_even_injective (out : Orient) {a b : List Digit}
    (haeven : Even a.length) (hbeven : Even b.length)
    (haback : backwardState out a = I) (hbback : backwardState out b = I)
    (hindex : indexLSB a ≠ indexLSB b) :
    coordinateLSB out a ≠ coordinateLSB out b := by
  obtain ⟨la, hla⟩ := haeven
  obtain ⟨lb, hlb⟩ := hbeven
  let ap := a ++ zeroPairs lb
  let bp := b ++ zeroPairs la
  have hlen : ap.length = bp.length := by
    simp [ap, bp, hla, hlb]
    omega
  have hcoordA : coordinateLSB out ap = coordinateLSB out a :=
    coordinateLSB_append_zeroPairs out a lb haback
  have hcoordB : coordinateLSB out bp = coordinateLSB out b :=
    coordinateLSB_append_zeroPairs out b la hbback
  intro hcoord
  have hp : ap = bp := coordinateLSB_injective out hlen (by simpa [hcoordA, hcoordB])
  apply hindex
  have hi := congrArg indexLSB hp
  simpa [ap, bp, indexLSB_append_zeroPairs] using hi

/-- A primitive positive time ratio forces coordinatewise scalar decomposition
of two planar chords satisfying the cross-multiplication equations. -/
theorem common_direction_of_cross (r s : ℕ) (u v : Vec2)
    (hr : r ≠ 0) (hrs : Nat.Coprime r s)
    (hx : (s : ℤ) * u.1 = (r : ℤ) * v.1)
    (hy : (s : ℤ) * u.2 = (r : ℤ) * v.2) :
    ∃ w : Vec2,
      u = ((r : ℤ) * w.1, (r : ℤ) * w.2) ∧
      v = ((s : ℤ) * w.1, (s : ℤ) * w.2) := by
  have hgcd : Int.gcd (r : ℤ) (s : ℤ) = 1 := by
    simpa [Int.gcd_eq_natAbs, Nat.coprime_iff_gcd_eq_one] using hrs
  have hdx : (r : ℤ) ∣ u.1 := by
    apply Int.dvd_of_dvd_mul_right_of_gcd_one _ hgcd
    exact ⟨v.1, hx⟩
  have hdy : (r : ℤ) ∣ u.2 := by
    apply Int.dvd_of_dvd_mul_right_of_gcd_one _ hgcd
    exact ⟨v.2, hy⟩
  obtain ⟨wx, hwx⟩ := hdx
  obtain ⟨wy, hwy⟩ := hdy
  refine ⟨(wx, wy), ?_, ?_⟩
  · exact Prod.ext hwx hwy
  · apply Prod.ext
    · have hrZ : (r : ℤ) ≠ 0 := by exact_mod_cast hr
      apply Int.eq_of_mul_eq_mul_left hrZ
      calc
        (r : ℤ) * v.1 = (s : ℤ) * u.1 := hx.symm
        _ = (s : ℤ) * ((r : ℤ) * wx) := by rw [hwx]
        _ = (r : ℤ) * ((s : ℤ) * wx) := by ring
    · have hrZ : (r : ℤ) ≠ 0 := by exact_mod_cast hr
      apply Int.eq_of_mul_eq_mul_left hrZ
      calc
        (r : ℤ) * v.2 = (s : ℤ) * u.2 := hy.symm
        _ = (s : ℤ) * ((r : ℤ) * wy) := by rw [hwy]
        _ = (r : ℤ) * ((s : ℤ) * wy) := by ring

/-- The three-gap valuation contradiction.  Once two adjacent planar chords
are odd scalar multiples of one common nonzero direction, the pair law for
the two gaps and their sum is impossible. -/
theorem three_gap_contradiction (r s g : ℕ) (w : Vec2)
    (hr : r ≠ 0) (hs : s ≠ 0) (hg : g ≠ 0) (hw : w ≠ (0,0))
    (hrodd : r % 2 = 1) (hsodd : s % 2 = 1)
    (h₁ : pairVal ((r : ℤ) * w.1, (r : ℤ) * w.2) = padicValNat 2 (r * g))
    (h₂ : pairVal ((s : ℤ) * w.1, (s : ℤ) * w.2) = padicValNat 2 (s * g))
    (h₃ : pairVal (((r + s : ℕ) : ℤ) * w.1, ((r + s : ℕ) : ℤ) * w.2) =
      padicValNat 2 ((r + s) * g)) : False := by
  have hvr : padicValNat 2 r = 0 := padicValNat_eq_zero_of_odd hrodd
  have hvs : padicValNat 2 s = 0 := padicValNat_eq_zero_of_odd hsodd
  have hrs : r + s ≠ 0 := by omega
  have hsumEven : 2 ∣ r + s := by omega
  have hvsum : padicValNat 2 (r + s) ≠ 0 := by
    intro hz
    rw [padicValNat.eq_zero_iff] at hz
    rcases hz with hbad | hzero | hnotdvd
    · omega
    · exact hrs hzero
    · exact hnotdvd hsumEven
  have hscale₁ := pairVal_nsmul r w hr hw
  have hscale₃ := pairVal_nsmul (r + s) w hrs hw
  rw [padicValNat.mul hr hg, hvr] at h₁
  rw [padicValNat.mul hrs hg] at h₃
  have hvw : pairVal w = padicValNat 2 g := by omega
  rw [hscale₃, hvw] at h₃
  omega

/-- Pair laws for two adjacent gaps and their sum rule out the exact
cross-multiplication equations imposed by collinearity after the time lift. -/
theorem no_collinear_from_pair_laws (A B : ℕ) (u v : Vec2)
    (hA : A ≠ 0) (hB : B ≠ 0) (hu0 : u ≠ (0,0)) (hv0 : v ≠ (0,0))
    (hx : (B : ℤ) * u.1 = (A : ℤ) * v.1)
    (hy : (B : ℤ) * u.2 = (A : ℤ) * v.2)
    (hU : pairVal u = padicValNat 2 A)
    (hV : pairVal v = padicValNat 2 B)
    (hUV : pairVal (u.1 + v.1, u.2 + v.2) = padicValNat 2 (A + B)) :
    False := by
  have hscaleA := pairVal_nsmul A v hA hv0
  have hscaleB := pairVal_nsmul B u hB hu0
  have hscaled :
      ((B : ℤ) * u.1, (B : ℤ) * u.2) =
        ((A : ℤ) * v.1, (A : ℤ) * v.2) := Prod.ext hx hy
  have hval : padicValNat 2 A = padicValNat 2 B := by
    rw [hscaled, hscaleA] at hscaleB
    rw [hU, hV] at hscaleB
    omega
  let g := Nat.gcd A B
  let r := A / g
  let s := B / g
  have hg : g ≠ 0 := Nat.gcd_ne_zero_left hA
  have hgA : g ∣ A := Nat.gcd_dvd_left A B
  have hgB : g ∣ B := Nat.gcd_dvd_right A B
  have hAr : A = r * g := (Nat.div_mul_cancel hgA).symm
  have hBs : B = s * g := (Nat.div_mul_cancel hgB).symm
  have hr : r ≠ 0 := by
    intro hz
    rw [hAr, hz, zero_mul] at hA
    exact hA rfl
  have hs : s ≠ 0 := by
    intro hz
    rw [hBs, hz, zero_mul] at hB
    exact hB rfl
  have hrs : Nat.Coprime r s := by
    exact Nat.coprime_div_gcd_div_gcd (Nat.gcd_pos_of_pos_left B (Nat.pos_of_ne_zero hA))
  have hvrvs : padicValNat 2 r = padicValNat 2 s := by
    rw [hAr, hBs, padicValNat.mul hr hg, padicValNat.mul hs hg] at hval
    omega
  have hvr : padicValNat 2 r = 0 := by
    by_contra hnonzero
    have hdr : 2 ∣ r := by
      by_contra hnd
      exact hnonzero (padicValNat.eq_zero_of_not_dvd hnd)
    have hds : 2 ∣ s := by
      by_contra hnd
      have hz := padicValNat.eq_zero_of_not_dvd hnd
      exact hnonzero (hvrvs.trans hz)
    have hdg : 2 ∣ Nat.gcd r s := Nat.dvd_gcd hdr hds
    rw [hrs.gcd_eq_one] at hdg
    omega
  have hvs : padicValNat 2 s = 0 := hvrvs.symm.trans hvr
  have hrodd : r % 2 = 1 := by
    apply Nat.mod_two_ne_zero.mp
    intro hm
    have hd : 2 ∣ r := Nat.dvd_iff_mod_eq_zero.mpr hm
    rw [padicValNat.eq_zero_iff] at hvr
    rcases hvr with hbad | hzero | hnot
    · omega
    · exact hr hzero
    · exact hnot hd
  have hsodd : s % 2 = 1 := by
    apply Nat.mod_two_ne_zero.mp
    intro hm
    have hd : 2 ∣ s := Nat.dvd_iff_mod_eq_zero.mpr hm
    rw [padicValNat.eq_zero_iff] at hvs
    rcases hvs with hbad | hzero | hnot
    · omega
    · exact hs hzero
    · exact hnot hd
  have hcrossR : (s : ℤ) * u.1 = (r : ℤ) * v.1 := by
    have hgZ : (g : ℤ) ≠ 0 := by exact_mod_cast hg
    apply Int.eq_of_mul_eq_mul_left hgZ
    calc
      (g : ℤ) * ((s : ℤ) * u.1) = ((s * g : ℕ) : ℤ) * u.1 := by push_cast; ring
      _ = (B : ℤ) * u.1 := by rw [← hBs]
      _ = (A : ℤ) * v.1 := hx
      _ = ((r * g : ℕ) : ℤ) * v.1 := by rw [← hAr]
      _ = (g : ℤ) * ((r : ℤ) * v.1) := by push_cast; ring
  have hcrossS : (s : ℤ) * u.2 = (r : ℤ) * v.2 := by
    have hgZ : (g : ℤ) ≠ 0 := by exact_mod_cast hg
    apply Int.eq_of_mul_eq_mul_left hgZ
    calc
      (g : ℤ) * ((s : ℤ) * u.2) = ((s * g : ℕ) : ℤ) * u.2 := by push_cast; ring
      _ = (B : ℤ) * u.2 := by rw [← hBs]
      _ = (A : ℤ) * v.2 := hy
      _ = ((r * g : ℕ) : ℤ) * v.2 := by rw [← hAr]
      _ = (g : ℤ) * ((r : ℤ) * v.2) := by push_cast; ring
  obtain ⟨w, huw, hvw⟩ := common_direction_of_cross r s u v hr hrs hcrossR hcrossS
  have hw : w ≠ (0,0) := by
    intro hw0
    apply hu0
    rw [huw, hw0]
    simp
  apply three_gap_contradiction r s g w hr hs hg hw hrodd hsodd
  · simpa [huw, hAr] using hU
  · simpa [hvw, hBs] using hV
  · have hsum : A + B = (r + s) * g := by
      rw [hAr, hBs, Nat.add_mul]
    rw [hsum] at hUV
    have hchord :
        (u.1 + v.1, u.2 + v.2) =
          (((r + s : ℕ) : ℤ) * w.1, ((r + s : ℕ) : ℤ) * w.2) := by
      rw [huw, hvw]
      push_cast
      apply Prod.ext <;> simp <;> ring
    rw [hchord] at hUV
    exact hUV

end Hilbert193

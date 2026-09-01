import Hilbert193.PairLaw

namespace Hilbert193
open Orient


def digitOfNat (n : ℕ) : Digit :=
  match n % 4 with
  | 0 => .d0
  | 1 => .d1
  | 2 => .d2
  | _ => .d3

theorem Digit.toNat_digitOfNat {n : ℕ} (hn : n < 4) :
    (digitOfNat n).toNat = n := by
  interval_cases n <;> decide

def rawDigits (n : ℕ) : List Digit :=
  (Nat.digits 4 n).map digitOfNat

private theorem indexLSB_map_digitOfNat (ns : List ℕ)
    (hsmall : ∀ n ∈ ns, n < 4) :
    indexLSB (ns.map digitOfNat) = Nat.ofDigits 4 ns := by
  induction ns with
  | nil => rfl
  | cons n ns ih =>
      simp only [List.map_cons, indexLSB, Nat.ofDigits]
      rw [Digit.toNat_digitOfNat (hsmall n (by simp))]
      congr 1
      exact congrArg (fun z => 4 * z) (ih (fun x hx => hsmall x (by simp [hx])))

@[simp] theorem indexLSB_rawDigits (n : ℕ) : indexLSB (rawDigits n) = n := by
  rw [rawDigits, indexLSB_map_digitOfNat, Nat.ofDigits_digits]
  intro d hd
  exact Nat.digits_lt_base (by omega) hd

private theorem indexLSB_append_d0 (ds : List Digit) :
    indexLSB (ds ++ [.d0]) = indexLSB ds := by
  induction ds with
  | nil => rfl
  | cons d ds ih => simp [indexLSB, ih]

/-- Add one high zero digit exactly when needed to make the digit count even. -/
def evenDigits (n : ℕ) : List Digit :=
  let ds := rawDigits n
  if Even ds.length then ds else ds ++ [.d0]

@[simp] theorem indexLSB_evenDigits (n : ℕ) : indexLSB (evenDigits n) = n := by
  by_cases h : Even (rawDigits n).length
  · simp [evenDigits, h]
  · simp [evenDigits, h, indexLSB_append_d0]

theorem evenDigits_length_even (n : ℕ) : Even (evenDigits n).length := by
  by_cases h : Even (rawDigits n).length
  · simpa [evenDigits, h]
  · have hodd : Odd (rawDigits n).length := Nat.not_even_iff_odd.mp h
    obtain ⟨k, hk⟩ := hodd
    refine ⟨k + 1, ?_⟩
    simp [evenDigits, h, hk]
    omega

theorem wordParity_reverse (ds : List Digit) :
    wordParity ds.reverse = wordParity ds := by
  induction ds with
  | nil => rfl
  | cons d ds ih =>
      rw [List.reverse_cons, wordParity_append, ih]
      simp only [wordParity]
      rcases digitParity d with ⟨a,b⟩
      rcases wordParity ds with ⟨x,y⟩
      cases a <;> cases b <;> cases x <;> cases y <;> decide

/-- The two terminal-state parity bits of the even-padded word for `n`. -/
def hilbertState (n : ℕ) : BitPair := wordParity (evenDigits n)

/-- The terminal Hilbert orientation of the even-padded word for `n`. -/
def hilbertOrient (n : ℕ) : Orient := orientOfParity (hilbertState n)

/-- The nested infinite Hilbert point at index `n`. -/
def hilbertPlanar (n : ℕ) : ℕ × ℕ :=
  coordinateLSB (hilbertOrient n) (evenDigits n)

theorem hilbertWord_backward (n : ℕ) :
    backwardState (hilbertOrient n) (evenDigits n) = I := by
  have h := backwardState_run_reverse I (evenDigits n).reverse
  simpa [hilbertOrient, hilbertState, terminal, run_state_parity,
    wordParity_reverse] using h

theorem hilbert_same_state_pair_law {a b : ℕ} (hne : a ≠ b)
    (hstate : hilbertState a = hilbertState b) :
    pairVal
        (intDelta (hilbertPlanar a).1 (hilbertPlanar b).1,
          intDelta (hilbertPlanar a).2 (hilbertPlanar b).2) =
      padicValNat 2 (Int.natAbs ((a : ℤ) - b)) := by
  have horient : hilbertOrient a = hilbertOrient b := by
    simp [hilbertOrient, hstate]
  have hbback : backwardState (hilbertOrient a) (evenDigits b) = I := by
    rw [horient]
    exact hilbertWord_backward b
  have hp := pair_law_even_words (hilbertOrient a)
    (evenDigits_length_even a) (evenDigits_length_even b)
    (hilbertWord_backward a) hbback (by simpa using hne)
  change pairVal
      (intDelta (coordinateLSB (hilbertOrient a) (evenDigits a)).1
          (coordinateLSB (hilbertOrient b) (evenDigits b)).1,
        intDelta (coordinateLSB (hilbertOrient a) (evenDigits a)).2
          (coordinateLSB (hilbertOrient b) (evenDigits b)).2) =
    padicValNat 2 (Int.natAbs ((a : ℤ) - b))
  rw [← horient]
  simpa [coordinateDelta, indexDistance] using hp

theorem hilbertPlanar_ne_of_same_state {a b : ℕ} (hne : a ≠ b)
    (hstate : hilbertState a = hilbertState b) :
    hilbertPlanar a ≠ hilbertPlanar b := by
  have horient : hilbertOrient a = hilbertOrient b := by
    simp [hilbertOrient, hstate]
  have hbback : backwardState (hilbertOrient a) (evenDigits b) = I := by
    rw [horient]
    exact hilbertWord_backward b
  change coordinateLSB (hilbertOrient a) (evenDigits a) ≠
    coordinateLSB (hilbertOrient b) (evenDigits b)
  rw [← horient]
  exact coordinateLSB_even_injective (hilbertOrient a)
    (evenDigits_length_even a) (evenDigits_length_even b)
    (hilbertWord_backward a) hbback (by simpa using hne)
/-- Cyclic labels `I=0, S=1, C=2, T=3` for the four Hilbert states. -/
def stateLabel : BitPair → ℕ
  | (.zero, .zero) => 0
  | (.one, .zero) => 1
  | (.one, .one) => 2
  | (.zero, .one) => 3

/-- Matching Gray-code corner tag; for parity bits `(p₀,p₃)` this is `(p₃,p₀)`. -/
def stateTag (p : BitPair) : ℕ × ℕ := (p.2.toNat, p.1.toNat)

@[simp] theorem stateLabel_le_three (p : BitPair) : stateLabel p ≤ 3 := by
  rcases p with ⟨p₀,p₃⟩
  cases p₀ <;> cases p₃ <;> decide

/-- Every Hilbert point, doubled and tagged by its terminal state. -/
def taggedPlanar (n : ℕ) : Vec2 :=
  let h := hilbertPlanar n
  let u := stateTag (hilbertState n)
  (2 * (h.1 : ℤ) + u.1, 2 * (h.2 : ℤ) + u.2)

/-- The index with its terminal-state label appended as a base-4 digit. -/
def taggedHeight (n : ℕ) : ℕ := 4 * n + stateLabel (hilbertState n)

structure Point3 where
  x : ℤ
  y : ℤ
  z : ℤ
  deriving DecidableEq

/-- The explicit all-index state-tagged Hilbert lift. -/
def taggedLift (n : ℕ) : Point3 where
  x := (taggedPlanar n).1
  y := (taggedPlanar n).2
  z := taggedHeight n

/-- Exact ordered collinearity equations for points whose `z` coordinates
increase from `p` through `q` to `r`. -/
def OrderedCollinear (p q r : Point3) : Prop :=
  (r.z - q.z) * (q.x - p.x) = (q.z - p.z) * (r.x - q.x) ∧
  (r.z - q.z) * (q.y - p.y) = (q.z - p.z) * (r.y - q.y)

private theorem unequal_tag_pair_law (p q : BitPair) (hpq : p ≠ q)
    (X : Vec2) (d : ℤ) :
    pairVal
        (2 * X.1 + (stateTag p).1 - (stateTag q).1,
          2 * X.2 + (stateTag p).2 - (stateTag q).2) =
      padicValNat 2
        (Int.natAbs (4 * d + (stateLabel p : ℤ) - stateLabel q)) := by
  rcases p with ⟨p₀,p₃⟩
  rcases q with ⟨q₀,q₃⟩
  cases p₀ <;> cases p₃ <;> cases q₀ <;> cases q₃ <;>
    simp [stateTag, stateLabel, Bit.toNat] at hpq ⊢
  all_goals
    first
    | rw [pairVal_odd_even (by omega) (by omega),
          padicValNat_natAbs_eq_zero (by omega)]
    | rw [pairVal_even_odd (by omega) (by omega),
          padicValNat_natAbs_eq_zero (by omega)]
    | rw [pairVal_odd_odd (by omega) (by omega),
          padicValNat_natAbs_eq_one (by omega) (by omega)]

private theorem doubled_tags_ne (p q : BitPair) (hpq : p ≠ q)
    (X Y : ℕ × ℕ) :
    ((2 * (X.1 : ℤ) + (stateTag p).1,
        2 * (X.2 : ℤ) + (stateTag p).2) : Vec2) ≠
      (2 * (Y.1 : ℤ) + (stateTag q).1,
        2 * (Y.2 : ℤ) + (stateTag q).2) := by
  rcases p with ⟨p₀,p₃⟩
  rcases q with ⟨q₀,q₃⟩
  cases p₀ <;> cases p₃ <;> cases q₀ <;> cases q₃ <;>
    simp [stateTag, Bit.toNat] at hpq ⊢ <;> omega

theorem taggedPlanar_ne {a b : ℕ} (hne : a ≠ b) :
    taggedPlanar a ≠ taggedPlanar b := by
  by_cases hstate : hilbertState a = hilbertState b
  · intro htagged
    apply hilbertPlanar_ne_of_same_state hne hstate
    have htag := congrArg stateTag hstate
    apply Prod.ext
    · have hx := congrArg Prod.fst htagged
      simp [taggedPlanar, htag] at hx
      omega
    · have hy := congrArg Prod.snd htagged
      simp [taggedPlanar, htag] at hy
      omega
  · exact doubled_tags_ne (hilbertState a) (hilbertState b) hstate
      (hilbertPlanar a) (hilbertPlanar b)

/-- The state tags extend the Hilbert pair law from equal terminal states to
all distinct indices. -/
theorem tagged_pair_law {a b : ℕ} (hne : a ≠ b) :
    pairVal
        ((taggedPlanar a).1 - (taggedPlanar b).1,
          (taggedPlanar a).2 - (taggedPlanar b).2) =
      padicValNat 2
        (Int.natAbs ((taggedHeight a : ℤ) - taggedHeight b)) := by
  by_cases hstate : hilbertState a = hilbertState b
  · let u : Vec2 :=
      (intDelta (hilbertPlanar a).1 (hilbertPlanar b).1,
        intDelta (hilbertPlanar a).2 (hilbertPlanar b).2)
    have hu : u ≠ (0, 0) := by
      intro hu0
      have hx := congrArg Prod.fst hu0
      have hy := congrArg Prod.snd hu0
      simp [u, intDelta] at hx hy
      apply hilbertPlanar_ne_of_same_state hne hstate
      apply Prod.ext <;> omega
    have hp := hilbert_same_state_pair_law hne hstate
    have hs := pairVal_nsmul 2 u (by decide) hu
    have hdist : Int.natAbs ((a : ℤ) - b) ≠ 0 := by
      intro h
      rw [Int.natAbs_eq_zero, sub_eq_zero] at h
      exact hne (by exact_mod_cast h)
    have hvfour :
        padicValNat 2 (4 * Int.natAbs ((a : ℤ) - b)) =
          padicValNat 2 (Int.natAbs ((a : ℤ) - b)) + 2 := by
      rw [padicValNat.mul (by decide) hdist]
      have h4 : padicValNat 2 4 = 2 := by
        rw [show 4 = 2 * 2 by norm_num, padicValNat.mul (by decide) (by decide),
          padicValNat_base (by decide)]
      rw [h4]
      omega
    have htag := congrArg stateTag hstate
    have hlabel := congrArg stateLabel hstate
    have hplanar :
        ((taggedPlanar a).1 - (taggedPlanar b).1,
          (taggedPlanar a).2 - (taggedPlanar b).2) =
        ((2 : ℤ) * u.1, (2 : ℤ) * u.2) := by
      apply Prod.ext
      · simp [taggedPlanar, htag, u, intDelta]
        ring
      · simp [taggedPlanar, htag, u, intDelta]
        ring
    have hheight :
        Int.natAbs ((taggedHeight a : ℤ) - taggedHeight b) =
          4 * Int.natAbs ((a : ℤ) - b) := by
      simp only [taggedHeight]
      rw [hlabel]
      push_cast
      rw [show
          (4 : ℤ) * a + stateLabel (hilbertState b) -
              ((4 : ℤ) * b + stateLabel (hilbertState b)) =
            4 * ((a : ℤ) - b) by ring,
        Int.natAbs_mul]
      norm_num
    rw [hplanar, hheight]
    rw [padicValNat_base (by decide)] at hs
    norm_num at hs
    rw [hs, hp, hvfour]
  · convert unequal_tag_pair_law (hilbertState a) (hilbertState b) hstate
      (intDelta (hilbertPlanar a).1 (hilbertPlanar b).1,
        intDelta (hilbertPlanar a).2 (hilbertPlanar b).2)
      ((a : ℤ) - b) using 1 <;>
        simp [taggedPlanar, taggedHeight, intDelta] <;> ring

/-- Consecutive tagged heights increase by between one and seven. -/
theorem taggedHeight_succ_bounds (n : ℕ) :
    1 ≤ taggedHeight (n + 1) - taggedHeight n ∧
      taggedHeight (n + 1) - taggedHeight n ≤ 7 := by
  have ha := stateLabel_le_three (hilbertState n)
  have hb := stateLabel_le_three (hilbertState (n + 1))
  unfold taggedHeight
  omega

theorem taggedHeight_strictMono : StrictMono taggedHeight := by
  apply strictMono_nat_of_lt_succ
  intro n
  have h := taggedHeight_succ_bounds n
  omega

/-- No three points of the explicit state-tagged Hilbert lift are collinear. -/
theorem taggedLift_no_three {i j k : ℕ} (hij : i < j) (hjk : j < k) :
    ¬OrderedCollinear (taggedLift i) (taggedLift j) (taggedLift k) := by
  intro hcol
  let ni := taggedHeight i
  let nj := taggedHeight j
  let nk := taggedHeight k
  have hnij : ni < nj := taggedHeight_strictMono hij
  have hnjk : nj < nk := taggedHeight_strictMono hjk
  let A := nj - ni
  let B := nk - nj
  have hA : A ≠ 0 := by omega
  have hB : B ≠ 0 := by omega
  let u : Vec2 :=
    ((taggedPlanar j).1 - (taggedPlanar i).1,
      (taggedPlanar j).2 - (taggedPlanar i).2)
  let v : Vec2 :=
    ((taggedPlanar k).1 - (taggedPlanar j).1,
      (taggedPlanar k).2 - (taggedPlanar j).2)
  have hu0 : u ≠ (0,0) := by
    intro hu
    apply taggedPlanar_ne (ne_of_gt hij)
    apply Prod.ext
    · have hx := congrArg Prod.fst hu
      simp [u] at hx
      omega
    · have hy := congrArg Prod.snd hu
      simp [u] at hy
      omega
  have hv0 : v ≠ (0,0) := by
    intro hv
    apply taggedPlanar_ne (ne_of_gt hjk)
    apply Prod.ext
    · have hx := congrArg Prod.fst hv
      simp [v] at hx
      omega
    · have hy := congrArg Prod.snd hv
      simp [v] at hy
      omega
  have hcastA : (A : ℤ) = (nj : ℤ) - ni := by omega
  have hcastB : (B : ℤ) = (nk : ℤ) - nj := by omega
  have hx : (B : ℤ) * u.1 = (A : ℤ) * v.1 := by
    rcases hcol with ⟨hcolx, _⟩
    simpa [OrderedCollinear, taggedLift, ni, nj, nk, u, v, hcastA, hcastB] using hcolx
  have hy : (B : ℤ) * u.2 = (A : ℤ) * v.2 := by
    rcases hcol with ⟨_, hcoly⟩
    simpa [OrderedCollinear, taggedLift, ni, nj, nk, u, v, hcastA, hcastB] using hcoly
  have hU : pairVal u = padicValNat 2 A := by
    have hp := tagged_pair_law (a := j) (b := i) (ne_of_gt hij)
    have hgap :
        Int.natAbs ((taggedHeight j : ℤ) - taggedHeight i) = A := by
      apply Nat.cast_injective (R := ℤ)
      rw [Int.natAbs_of_nonneg]
      · exact hcastA.symm
      · change 0 ≤ (nj : ℤ) - ni
        omega
    simpa [u, hgap] using hp
  have hV : pairVal v = padicValNat 2 B := by
    have hp := tagged_pair_law (a := k) (b := j) (ne_of_gt hjk)
    have hgap :
        Int.natAbs ((taggedHeight k : ℤ) - taggedHeight j) = B := by
      apply Nat.cast_injective (R := ℤ)
      rw [Int.natAbs_of_nonneg]
      · exact hcastB.symm
      · change 0 ≤ (nk : ℤ) - nj
        omega
    simpa [v, hgap] using hp
  have hUV : pairVal (u.1 + v.1, u.2 + v.2) = padicValNat 2 (A + B) := by
    have hp := tagged_pair_law (a := k) (b := i) (ne_of_gt (lt_trans hij hjk))
    have hgap :
        Int.natAbs ((taggedHeight k : ℤ) - taggedHeight i) = A + B := by
      apply Nat.cast_injective (R := ℤ)
      rw [Int.natAbs_of_nonneg]
      · push_cast
        rw [hcastA, hcastB]
        ring
      · change 0 ≤ (nk : ℤ) - ni
        omega
    rw [hgap] at hp
    have hchord :
        (u.1 + v.1, u.2 + v.2) =
          ((taggedPlanar k).1 - (taggedPlanar i).1,
            (taggedPlanar k).2 - (taggedPlanar i).2) := by
      apply Prod.ext <;> simp [u, v] <;> ring
    rw [hchord]
    exact hp
  exact no_collinear_from_pair_laws A B u v hA hB hu0 hv0 hx hy hU hV hUV

end Hilbert193

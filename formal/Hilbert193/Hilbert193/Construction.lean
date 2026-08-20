import Hilbert193.PairLaw

namespace Hilbert193
open Orient

/-- Numeric value of the two-digit suffix used to cancel a terminal parity. -/
def steeringValue : BitPair → ℕ
  | (.zero, .zero) => 5   -- `11₄`
  | (.one, .zero) => 1    -- `01₄`
  | (.zero, .one) => 13   -- `31₄`
  | (.one, .one) => 3     -- `03₄`

@[simp] theorem steeringValue_bounds (p : BitPair) :
    1 ≤ steeringValue p ∧ steeringValue p ≤ 13 := by
  rcases p with ⟨p₀,p₃⟩
  cases p₀ <;> cases p₃ <;> decide

/-- One representative in every consecutive block of sixteen Hilbert indices. -/
def selectedIndex (state : ℕ → BitPair) (a : ℕ) : ℕ :=
  16 * a + steeringValue (state a)

/-- Consecutive representatives have index gap between 4 and 28. -/
theorem selectedIndex_succ_gap (state : ℕ → BitPair) (a : ℕ) :
    ∃ gap, 4 ≤ gap ∧ gap ≤ 28 ∧
      selectedIndex state (a + 1) = selectedIndex state a + gap := by
  have ha := steeringValue_bounds (state a)
  have hb := steeringValue_bounds (state (a + 1))
  refine ⟨16 + steeringValue (state (a + 1)) - steeringValue (state a), ?_⟩
  unfold selectedIndex
  omega

/-- The selected indices are strictly increasing. -/
theorem selectedIndex_strictMono (state : ℕ → BitPair) :
    StrictMono (selectedIndex state) := by
  apply strictMono_nat_of_lt_succ
  intro a
  obtain ⟨gap, hgap, _, heq⟩ := selectedIndex_succ_gap state a
  omega


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
private theorem indexLSB_map_digitOfNat (ns : List ℕ) (hsmall : ∀ n ∈ ns, n < 4) :
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

@[simp] theorem steeringDigits_length (p : BitPair) :
    (steeringDigits p).length = 2 := by
  rcases p with ⟨p₀,p₃⟩
  cases p₀ <;> cases p₃ <;> rfl

@[simp] theorem indexLSB_steering_reverse (p : BitPair) :
    indexLSB (steeringDigits p).reverse = steeringValue p := by
  rcases p with ⟨p₀,p₃⟩
  cases p₀ <;> cases p₃ <;> decide

theorem indexLSB_append (a b : List Digit) :
    indexLSB (a ++ b) = indexLSB a + 4 ^ a.length * indexLSB b := by
  induction a with
  | nil => simp [indexLSB]
  | cons d ds ih =>
      simp only [List.cons_append, indexLSB, List.length_cons, Nat.pow_succ, ih]
      ring

/-- Least-significant-first base-4 word of the selected Hilbert index in block `a`. -/
def selectedWord (a : ℕ) : List Digit :=
  let pfx := evenDigits a
  (steeringDigits (wordParity pfx)).reverse ++ pfx

def selectedState (a : ℕ) : BitPair := wordParity (evenDigits a)

@[simp] theorem selectedWord_index (a : ℕ) :
    indexLSB (selectedWord a) = selectedIndex selectedState a := by
  simp [selectedWord, selectedIndex, selectedState, indexLSB_append]
  ring

theorem selectedWord_length_even (a : ℕ) : Even (selectedWord a).length := by
  obtain ⟨k, hk⟩ := evenDigits_length_even a
  refine ⟨k + 1, ?_⟩
  simp [selectedWord, hk]
  omega

theorem selectedWord_terminal (a : ℕ) :
    terminal (selectedWord a).reverse = I := by
  simp only [selectedWord, List.reverse_append, List.reverse_reverse]
  rw [← wordParity_reverse (evenDigits a)]
  exact terminal_steered (evenDigits a).reverse

theorem selectedWord_backward (a : ℕ) :
    backwardState I (selectedWord a) = I := by
  have h := backwardState_run_reverse I (selectedWord a).reverse
  rw [show (run I (selectedWord a).reverse).2 = I by
    exact selectedWord_terminal a, List.reverse_reverse] at h
  exact h

/-- Planar point of the selected Hilbert index. -/
def selectedPlanar (a : ℕ) : ℕ × ℕ :=
  coordinateLSB I (selectedWord a)

theorem selected_pair_law {a b : ℕ} (hne : a ≠ b) :
    pairVal
        (intDelta (selectedPlanar a).1 (selectedPlanar b).1,
          intDelta (selectedPlanar a).2 (selectedPlanar b).2) =
      padicValNat 2 (Int.natAbs ((selectedIndex selectedState a : ℤ) -
        selectedIndex selectedState b)) := by
  have hindex : indexLSB (selectedWord a) ≠ indexLSB (selectedWord b) := by
    rw [selectedWord_index, selectedWord_index]
    exact (selectedIndex_strictMono selectedState).injective.ne hne

  have hp := pair_law_even_words (selectedWord_length_even a)
    (selectedWord_length_even b) (selectedWord_backward a) (selectedWord_backward b) hindex
  simpa [selectedPlanar, coordinateDelta, indexDistance, selectedWord_index] using hp

theorem selectedPlanar_ne {a b : ℕ} (hne : a ≠ b) :
    selectedPlanar a ≠ selectedPlanar b := by
  apply coordinateLSB_even_injective (selectedWord_length_even a)
    (selectedWord_length_even b) (selectedWord_backward a) (selectedWord_backward b)
  rw [selectedWord_index, selectedWord_index]
  exact (selectedIndex_strictMono selectedState).injective.ne hne

structure Point3 where
  x : ℤ
  y : ℤ
  z : ℤ
  deriving DecidableEq

/-- The explicit time-lifted selected Hilbert walk. -/
def selectedLift (a : ℕ) : Point3 where
  x := (selectedPlanar a).1
  y := (selectedPlanar a).2
  z := selectedIndex selectedState a

/-- Exact ordered collinearity equations for points whose `z` coordinates
increase from `p` through `q` to `r`. -/
def OrderedCollinear (p q r : Point3) : Prop :=
  (r.z - q.z) * (q.x - p.x) = (q.z - p.z) * (r.x - q.x) ∧
  (r.z - q.z) * (q.y - p.y) = (q.z - p.z) * (r.y - q.y)

/-- No three points of the explicit selected time-lifted Hilbert walk are collinear. -/
theorem selectedLift_no_three {i j k : ℕ} (hij : i < j) (hjk : j < k) :
    ¬OrderedCollinear (selectedLift i) (selectedLift j) (selectedLift k) := by
  intro hcol
  let ni := selectedIndex selectedState i
  let nj := selectedIndex selectedState j
  let nk := selectedIndex selectedState k
  have hnij : ni < nj := selectedIndex_strictMono selectedState hij
  have hnjk : nj < nk := selectedIndex_strictMono selectedState hjk
  let A := nj - ni
  let B := nk - nj
  have hA : A ≠ 0 := by omega
  have hB : B ≠ 0 := by omega
  let u : Vec2 :=
    (intDelta (selectedPlanar j).1 (selectedPlanar i).1,
      intDelta (selectedPlanar j).2 (selectedPlanar i).2)
  let v : Vec2 :=
    (intDelta (selectedPlanar k).1 (selectedPlanar j).1,
      intDelta (selectedPlanar k).2 (selectedPlanar j).2)
  have hu0 : u ≠ (0,0) := by
    intro hu
    have hx := congrArg Prod.fst hu
    have hy := congrArg Prod.snd hu
    simp [u, intDelta] at hx hy
    apply selectedPlanar_ne (ne_of_lt hij)
    apply Prod.ext <;> omega
  have hv0 : v ≠ (0,0) := by
    intro hv
    have hx := congrArg Prod.fst hv
    have hy := congrArg Prod.snd hv
    simp [v, intDelta] at hx hy
    apply selectedPlanar_ne (ne_of_lt hjk)
    apply Prod.ext <;> omega
  have hcastA : (A : ℤ) = (nj : ℤ) - ni := by omega
  have hcastB : (B : ℤ) = (nk : ℤ) - nj := by omega
  have hx : (B : ℤ) * u.1 = (A : ℤ) * v.1 := by
    rcases hcol with ⟨hcolx, hcoly⟩
    simpa [OrderedCollinear, selectedLift, ni, nj, nk, u, v, hcastA, hcastB,
      intDelta] using hcolx
  have hy : (B : ℤ) * u.2 = (A : ℤ) * v.2 := by
    rcases hcol with ⟨hcolx, hcoly⟩
    simpa [OrderedCollinear, selectedLift, ni, nj, nk, u, v, hcastA, hcastB,
      intDelta] using hcoly
  have hU : pairVal u = padicValNat 2 A := by
    have hp := selected_pair_law (a := j) (b := i) (ne_of_gt hij)
    have hgap : Int.natAbs ((nj : ℤ) - ni) = A := by
      apply Nat.cast_injective (R := ℤ)
      rw [Int.natAbs_of_nonneg (by omega)]
      exact hcastA.symm
    rw [hgap] at hp
    exact hp
  have hV : pairVal v = padicValNat 2 B := by
    have hp := selected_pair_law (a := k) (b := j) (ne_of_gt hjk)
    have hgap : Int.natAbs ((nk : ℤ) - nj) = B := by
      apply Nat.cast_injective (R := ℤ)
      rw [Int.natAbs_of_nonneg (by omega)]
      exact hcastB.symm
    rw [hgap] at hp
    exact hp
  have hUV : pairVal (u.1 + v.1, u.2 + v.2) = padicValNat 2 (A + B) := by
    have hp := selected_pair_law (a := k) (b := i) (ne_of_gt (lt_trans hij hjk))
    have hgap : Int.natAbs ((nk : ℤ) - ni) = A + B := by
      apply Nat.cast_injective (R := ℤ)
      rw [Int.natAbs_of_nonneg (by omega)]
      push_cast
      omega
    rw [hgap] at hp
    have hchord :
        (u.1 + v.1, u.2 + v.2) =
          (intDelta (selectedPlanar k).1 (selectedPlanar i).1,
            intDelta (selectedPlanar k).2 (selectedPlanar i).2) := by
      apply Prod.ext
      · change
          intDelta (selectedPlanar j).1 (selectedPlanar i).1 +
              intDelta (selectedPlanar k).1 (selectedPlanar j).1 =
            intDelta (selectedPlanar k).1 (selectedPlanar i).1
        unfold intDelta
        ring
      · change
          intDelta (selectedPlanar j).2 (selectedPlanar i).2 +
              intDelta (selectedPlanar k).2 (selectedPlanar j).2 =
            intDelta (selectedPlanar k).2 (selectedPlanar i).2
        unfold intDelta
        ring
    rw [hchord]
    exact hp
  exact no_collinear_from_pair_laws A B u v hA hB hu0 hv0 hx hy hU hV hUV
end Hilbert193

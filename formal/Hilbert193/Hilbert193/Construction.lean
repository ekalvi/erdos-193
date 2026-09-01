import Hilbert193.Gaussian

/-! Matching planar and height tags and the no-collinearity obstruction. -/

namespace Hilbert193

/-- Double the Gaussian point and append its direction as a Gray-code corner. -/
def taggedPlanar (n : ℕ) : Vec2 :=
  (2 * (gaussianPlanar n).1 + (gaussianState n).tag.1,
    2 * (gaussianPlanar n).2 + (gaussianState n).tag.2)

/-- Append the same direction state as the low base-4 height digit. -/
def taggedHeight (n : ℕ) : ℕ := 4 * n + (gaussianState n).label

@[ext] structure Point3 where
  x : ℤ
  y : ℤ
  z : ℤ
  deriving DecidableEq, Repr

/-- The explicit all-index Gaussian-lattice lift. -/
def taggedLift (n : ℕ) : Point3 where
  x := (taggedPlanar n).1
  y := (taggedPlanar n).2
  z := taggedHeight n

/-- Exact ordered collinearity equations for increasing heights. -/
def OrderedCollinear (p q r : Point3) : Prop :=
  (r.z - q.z) * (q.x - p.x) = (q.z - p.z) * (r.x - q.x) ∧
  (r.z - q.z) * (q.y - p.y) = (q.z - p.z) * (r.y - q.y)

private theorem doubled_tags_ne (p q : Direction) (hpq : p ≠ q) (X Y : Vec2) :
    ((2 * X.1 + p.tag.1, 2 * X.2 + p.tag.2) : Vec2) ≠
      (2 * Y.1 + q.tag.1, 2 * Y.2 + q.tag.2) := by
  cases p <;> cases q <;> simp [Direction.tag] at hpq ⊢ <;> omega

theorem taggedPlanar_ne {m n : ℕ} (hmn : m < n) : taggedPlanar m ≠ taggedPlanar n := by
  by_cases hs : gaussianState m = gaussianState n
  · intro htag
    apply gaussianPlanar_ne_of_same_state hmn hs
    apply Prod.ext
    · have hx := congrArg Prod.fst htag
      simp [taggedPlanar, hs] at hx
      omega
    · have hy := congrArg Prod.snd htag
      simp [taggedPlanar, hs] at hy
      omega
  · exact doubled_tags_ne (gaussianState m) (gaussianState n) hs
      (gaussianPlanar m) (gaussianPlanar n)

private theorem unequal_tag_pair_law (p q : Direction) (hpq : p ≠ q)
    (X : Vec2) (d : ℕ) (hd : d ≠ 0) :
    pairVal
        (2 * X.1 + q.tag.1 - p.tag.1,
          2 * X.2 + q.tag.2 - p.tag.2) =
      padicValNat 2 (4 * d + q.label - p.label) := by
  cases p <;> cases q <;>
    simp [Direction.tag, Direction.label] at hpq ⊢
  all_goals
    try rw [pairVal_eq_zero_of_sum_not_two_dvd (by omega),
      padicValNat.eq_zero_of_not_dvd (by omega)]
  all_goals
    rw [pairVal_odd_odd (by omega) (by omega)]
    symm
    apply padicValNat_eq_one_of_two_dvd_not_four <;> omega

private theorem padicValNat_four_mul (d : ℕ) (hd : d ≠ 0) :
    padicValNat 2 (4 * d) = padicValNat 2 d + 2 := by
  rw [show 4 * d = 2 * (2 * d) by ring,
    padicValNat.mul (by decide) (mul_ne_zero (by decide) hd),
    padicValNat.mul (by decide) hd, padicValNat_base (by decide)]
  omega

/-- The matching tags extend the Gaussian pair law to every ordered pair. -/
theorem tagged_pair_law {m n : ℕ} (hmn : m < n) :
    pairVal (subVec (taggedPlanar n) (taggedPlanar m)) =
      padicValNat 2 (taggedHeight n - taggedHeight m) := by
  by_cases hs : gaussianState m = gaussianState n
  · let u := subVec (gaussianPlanar n) (gaussianPlanar m)
    have hu : u ≠ (0, 0) := by
      intro h
      apply gaussianPlanar_ne_of_same_state hmn hs
      apply Prod.ext
      · have hx := congrArg Prod.fst h
        simp [u, subVec] at hx
        omega
      · have hy := congrArg Prod.snd h
        simp [u, subVec] at hy
        omega
    have hp := gaussian_same_state_pair_law hmn hs
    have hscale := pairVal_nsmul 2 u (by decide) hu
    have hplanar : subVec (taggedPlanar n) (taggedPlanar m) = (2 * u.1, 2 * u.2) := by
      apply Prod.ext <;> simp [taggedPlanar, subVec, u, hs] <;> ring
    have hheight : taggedHeight n - taggedHeight m = 4 * (n - m) := by
      simp [taggedHeight, hs]
      omega
    rw [hplanar, hheight]
    calc
      pairVal (2 * u.1, 2 * u.2) = pairVal u + 2 := by
        simpa using hscale
      _ = padicValNat 2 (4 * (n - m)) := by
        rw [hp, padicValNat_four_mul (n - m) (by omega)]
  · let X := subVec (gaussianPlanar n) (gaussianPlanar m)
    have hp := unequal_tag_pair_law (gaussianState m) (gaussianState n) hs X
      (n - m) (by omega)
    have hplanar :
        subVec (taggedPlanar n) (taggedPlanar m) =
          (2 * X.1 + (gaussianState n).tag.1 - (gaussianState m).tag.1,
            2 * X.2 + (gaussianState n).tag.2 - (gaussianState m).tag.2) := by
      apply Prod.ext <;> simp [taggedPlanar, subVec, X] <;> ring
    have hheight :
        taggedHeight n - taggedHeight m =
          4 * (n - m) + (gaussianState n).label - (gaussianState m).label := by
      have hm := Direction.label_le_three (gaussianState m)
      have hn := Direction.label_le_three (gaussianState n)
      simp [taggedHeight]
      omega
    rw [hplanar, hheight]
    exact hp

/-- Consecutive tagged heights increase by between one and seven. -/
theorem taggedHeight_succ_bounds (n : ℕ) :
    1 ≤ taggedHeight (n + 1) - taggedHeight n ∧
      taggedHeight (n + 1) - taggedHeight n ≤ 7 := by
  have ha := Direction.label_le_three (gaussianState n)
  have hb := Direction.label_le_three (gaussianState (n + 1))
  unfold taggedHeight
  omega

theorem taggedHeight_strictMono : StrictMono taggedHeight := by
  apply strictMono_nat_of_lt_succ
  intro n
  have h := taggedHeight_succ_bounds n
  omega

private theorem unequal_sum_valuation {A B : ℕ} (hA : A ≠ 0) (hB : B ≠ 0)
    (hAB : padicValNat 2 A = padicValNat 2 B) :
    padicValNat 2 (A + B) ≠ padicValNat 2 B := by
  let g := Nat.gcd A B
  let r := A / g
  let s := B / g
  have hg : g ≠ 0 := Nat.gcd_ne_zero_left hA
  have hgA : g ∣ A := Nat.gcd_dvd_left A B
  have hgB : g ∣ B := Nat.gcd_dvd_right A B
  have hAr : A = r * g := (Nat.div_mul_cancel hgA).symm
  have hBs : B = s * g := (Nat.div_mul_cancel hgB).symm
  have hr : r ≠ 0 := by intro h; rw [hAr, h, zero_mul] at hA; exact hA rfl
  have hs : s ≠ 0 := by intro h; rw [hBs, h, zero_mul] at hB; exact hB rfl
  have hrs : Nat.Coprime r s :=
    Nat.coprime_div_gcd_div_gcd (Nat.gcd_pos_of_pos_left B (Nat.pos_of_ne_zero hA))
  have hvrvs : padicValNat 2 r = padicValNat 2 s := by
    rw [hAr, hBs, padicValNat.mul hr hg, padicValNat.mul hs hg] at hAB
    omega
  have hvr : padicValNat 2 r = 0 := by
    by_contra hn
    have hdr : 2 ∣ r := by
      by_contra hnd
      exact hn (padicValNat.eq_zero_of_not_dvd hnd)
    have hds : 2 ∣ s := by
      by_contra hnd
      exact hn (hvrvs.trans (padicValNat.eq_zero_of_not_dvd hnd))
    have : 2 ∣ Nat.gcd r s := Nat.dvd_gcd hdr hds
    rw [hrs.gcd_eq_one] at this
    omega
  have hvs : padicValNat 2 s = 0 := hvrvs.symm.trans hvr
  have hrsEven : 2 ∣ r + s := by
    have hrodd : r % 2 = 1 := by
      apply Nat.mod_two_ne_zero.mp
      intro hm
      have hd : 2 ∣ r := Nat.dvd_iff_mod_eq_zero.mpr hm
      rw [padicValNat.eq_zero_iff] at hvr
      rcases hvr with hbad | hzero | hnot <;> omega
    have hsodd : s % 2 = 1 := by
      apply Nat.mod_two_ne_zero.mp
      intro hm
      have hd : 2 ∣ s := Nat.dvd_iff_mod_eq_zero.mpr hm
      rw [padicValNat.eq_zero_iff] at hvs
      rcases hvs with hbad | hzero | hnot <;> omega
    omega
  have hrs0 : r + s ≠ 0 := by
    intro h
    exact hr (Nat.eq_zero_of_add_eq_zero_right h)
  have hvsum : padicValNat 2 (r + s) ≠ 0 := by
    intro hz
    rw [padicValNat.eq_zero_iff] at hz
    rcases hz with hbad | hzero | hnot
    · omega
    · exact hrs0 hzero
    · exact hnot hrsEven
  intro heq
  have hsum : A + B = (r + s) * g := by rw [hAr, hBs, Nat.add_mul]
  rw [hsum, hBs, padicValNat.mul hrs0 hg, padicValNat.mul hs hg, hvs] at heq
  omega

/-- No three points of the explicit Gaussian tagged lift are collinear. -/
theorem taggedLift_no_three {i j k : ℕ} (hij : i < j) (hjk : j < k) :
    ¬OrderedCollinear (taggedLift i) (taggedLift j) (taggedLift k) := by
  intro hcol
  let A := taggedHeight j - taggedHeight i
  let B := taggedHeight k - taggedHeight j
  have hA : A ≠ 0 := by have := taggedHeight_strictMono hij; omega
  have hB : B ≠ 0 := by have := taggedHeight_strictMono hjk; omega
  let u := subVec (taggedPlanar j) (taggedPlanar i)
  let v := subVec (taggedPlanar k) (taggedPlanar j)
  have hu : u ≠ (0, 0) := by
    intro h
    apply taggedPlanar_ne hij
    apply Prod.ext <;> have := congrArg Prod.fst h <;> simp [u, subVec] at * <;> omega
  have hv : v ≠ (0, 0) := by
    intro h
    apply taggedPlanar_ne hjk
    apply Prod.ext <;> have := congrArg Prod.fst h <;> simp [v, subVec] at * <;> omega
  have huw : addVec u v ≠ (0, 0) := by
    intro h
    apply taggedPlanar_ne (lt_trans hij hjk)
    apply Prod.ext
    · have hx := congrArg Prod.fst h
      simp [u, v, addVec, subVec] at hx
      omega
    · have hy := congrArg Prod.snd h
      simp [u, v, addVec, subVec] at hy
      omega
  have hHeightIJ : taggedHeight i ≤ taggedHeight j := (taggedHeight_strictMono hij).le
  have hHeightJK : taggedHeight j ≤ taggedHeight k := (taggedHeight_strictMono hjk).le
  have hx : (B : ℤ) * u.1 = (A : ℤ) * v.1 := by
    rcases hcol with ⟨hx, _⟩
    dsimp [A, B, u, v]
    rw [Nat.cast_sub hHeightJK, Nat.cast_sub hHeightIJ]
    simpa [subVec, OrderedCollinear, taggedLift] using hx
  have hy : (B : ℤ) * u.2 = (A : ℤ) * v.2 := by
    rcases hcol with ⟨_, hy⟩
    dsimp [A, B, u, v]
    rw [Nat.cast_sub hHeightJK, Nat.cast_sub hHeightIJ]
    simpa [subVec, OrderedCollinear, taggedLift] using hy
  have hU : pairVal u = padicValNat 2 A := by simpa [u, A] using tagged_pair_law hij
  have hV : pairVal v = padicValNat 2 B := by simpa [v, B] using tagged_pair_law hjk
  have hUV : pairVal (addVec u v) = padicValNat 2 (A + B) := by
    have hp := tagged_pair_law (lt_trans hij hjk)
    have hgap : taggedHeight k - taggedHeight i = A + B := by
      have hi := taggedHeight_strictMono hij
      have hj := taggedHeight_strictMono hjk
      simp [A, B]
      omega
    rw [hgap] at hp
    have hchord : subVec (taggedPlanar k) (taggedPlanar i) = addVec u v := by
      apply Prod.ext <;> simp [u, v, addVec, subVec]
    rwa [hchord] at hp
  have hscaled :
      ((B : ℤ) * u.1, (B : ℤ) * u.2) = ((A : ℤ) * v.1, (A : ℤ) * v.2) :=
    Prod.ext hx hy
  have hscaleB := pairVal_nsmul B u hB hu
  have hscaleA := pairVal_nsmul A v hA hv
  rw [hscaled, hscaleA, hU, hV] at hscaleB
  have hAB : padicValNat 2 A = padicValNat 2 B := by omega
  have hscaledSum :
      ((B : ℤ) * (addVec u v).1, (B : ℤ) * (addVec u v).2) =
        (((A + B : ℕ) : ℤ) * v.1, ((A + B : ℕ) : ℤ) * v.2) := by
    apply Prod.ext <;> simp [addVec] <;> ring_nf at hx hy ⊢ <;> omega
  have hscaleSumB := pairVal_nsmul B (addVec u v) hB huw
  have hscaleSumAB := pairVal_nsmul (A + B) v (by omega) hv
  rw [hscaledSum, hscaleSumAB, hUV, hV] at hscaleSumB
  have hsumEq : padicValNat 2 (A + B) = padicValNat 2 B := by omega
  exact unequal_sum_valuation hA hB hAB hsumEq

end Hilbert193

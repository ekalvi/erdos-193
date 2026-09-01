import Mathlib.NumberTheory.Padics.PadicVal.Basic
import Mathlib.Algebra.Ring.Parity

/-! Two-adic squared-norm lemmas for the Gaussian-lattice construction. -/

namespace Hilbert193

abbrev Vec2 := ℤ × ℤ

def addVec (p q : Vec2) : Vec2 := (p.1 + q.1, p.2 + q.2)

def mulOnePlusI (p : Vec2) : Vec2 := (p.1 - p.2, p.1 + p.2)

def normSq (u : Vec2) : ℕ := Int.natAbs (u.1 * u.1 + u.2 * u.2)

def pairVal (u : Vec2) : ℕ := padicValNat 2 (normSq u)

@[simp] theorem normSq_zero : normSq (0, 0) = 0 := by simp [normSq]

@[simp] theorem pairVal_zero : pairVal (0, 0) = 0 := by simp [pairVal]

@[simp] theorem normSq_ne_zero {u : Vec2} (hu : u ≠ (0, 0)) : normSq u ≠ 0 := by
  rcases u with ⟨x, y⟩
  intro h
  simp only [normSq, Int.natAbs_eq_zero] at h
  have hx : x = 0 := by nlinarith [sq_nonneg x, sq_nonneg y]
  have hy : y = 0 := by nlinarith [sq_nonneg x, sq_nonneg y]
  exact hu (by simp [hx, hy])

@[simp] theorem normSq_neg (u : Vec2) : normSq (-u.1, -u.2) = normSq u := by
  simp [normSq]

@[simp] theorem pairVal_neg (u : Vec2) : pairVal (-u.1, -u.2) = pairVal u := by
  simp [pairVal]

private theorem normSq_nsmul (k : ℕ) (u : Vec2) :
    normSq ((k : ℤ) * u.1, (k : ℤ) * u.2) = k * k * normSq u := by
  rcases u with ⟨x, y⟩
  simp only [normSq]
  rw [show ((k : ℤ) * x) * ((k : ℤ) * x) + ((k : ℤ) * y) * ((k : ℤ) * y) =
      ((k : ℤ) * k) * (x * x + y * y) by ring]
  simp [Int.natAbs_mul]

/-- Multiplying a nonzero planar vector by `k` adds twice the 2-adic order of `k`. -/
theorem pairVal_nsmul (k : ℕ) (u : Vec2) (hk : k ≠ 0) (hu : u ≠ (0, 0)) :
    pairVal ((k : ℤ) * u.1, (k : ℤ) * u.2) = pairVal u + 2 * padicValNat 2 k := by
  have hnorm := normSq_ne_zero hu
  simp only [pairVal, normSq_nsmul]
  rw [padicValNat.mul (mul_ne_zero hk hk) hnorm, padicValNat.mul hk hk]
  omega

@[simp] theorem normSq_mulOnePlusI (u : Vec2) :
    normSq (mulOnePlusI u) = 2 * normSq u := by
  rcases u with ⟨x, y⟩
  simp only [mulOnePlusI, normSq]
  rw [show (x - y) * (x - y) + (x + y) * (x + y) =
      (2 : ℤ) * (x * x + y * y) by ring]
  simp [Int.natAbs_mul]

/-- Multiplication by `1+i` adds one to the norm valuation. -/
theorem pairVal_mulOnePlusI {u : Vec2} (hu : u ≠ (0, 0)) :
    pairVal (mulOnePlusI u) = pairVal u + 1 := by
  simp only [pairVal, normSq_mulOnePlusI]
  rw [padicValNat.mul (by decide) (normSq_ne_zero hu), padicValNat_base (by decide)]
  omega

private theorem two_dvd_sq_sub_self (x : ℤ) : (2 : ℤ) ∣ x * x - x := by
  obtain ⟨k, hk | hk⟩ := Int.even_or_odd' x
  · subst x
    refine ⟨2 * k * k - k, by ring⟩
  · subst x
    refine ⟨2 * k * k + k, by ring⟩

/-- If the coordinate sum is odd, then the squared norm is odd. -/
theorem normSq_not_two_dvd_of_sum_not_two_dvd {u : Vec2}
    (hsum : ¬(2 : ℤ) ∣ u.1 + u.2) : ¬2 ∣ normSq u := by
  intro hnorm
  have hnormZ : (2 : ℤ) ∣ u.1 * u.1 + u.2 * u.2 := by
    apply Int.dvd_natAbs.mp
    exact Int.natCast_dvd_natCast.mpr hnorm
  have hx := two_dvd_sq_sub_self u.1
  have hy := two_dvd_sq_sub_self u.2
  apply hsum
  obtain ⟨a, ha⟩ := hnormZ
  obtain ⟨b, hb⟩ := hx
  obtain ⟨c, hc⟩ := hy
  refine ⟨a - b - c, ?_⟩
  omega

/-- An odd coordinate sum gives valuation zero. -/
theorem pairVal_eq_zero_of_sum_not_two_dvd {u : Vec2}
    (hsum : ¬(2 : ℤ) ∣ u.1 + u.2) : pairVal u = 0 := by
  apply padicValNat.eq_zero_of_not_dvd
  exact normSq_not_two_dvd_of_sum_not_two_dvd hsum


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

theorem padicValNat_eq_one_of_two_dvd_not_four {n : ℕ}
    (htwo : 2 ∣ n) (hfour : ¬4 ∣ n) : padicValNat 2 n = 1 := by
  have h := padicValNat_natAbs_eq_one (z := (n : ℤ))
    (by exact_mod_cast htwo) (by exact_mod_cast hfour)
  simpa using h

theorem pairVal_odd_odd {x y : ℤ}
    (hx : ¬(2 : ℤ) ∣ x) (hy : ¬(2 : ℤ) ∣ y) :
    pairVal (x, y) = 1 := by
  obtain ⟨a, ha | ha⟩ := Int.even_or_odd' x
  · exfalso
    apply hx
    exact ⟨a, ha⟩
  obtain ⟨b, hb | hb⟩ := Int.even_or_odd' y
  · exfalso
    apply hy
    exact ⟨b, hb⟩
  subst x
  subst y
  unfold pairVal normSq
  apply padicValNat_natAbs_eq_one
  · refine ⟨2 * (a * a + a + b * b + b) + 1, by ring⟩
  · intro hfour
    obtain ⟨k, hk⟩ := hfour
    ring_nf at hk
    omega

end Hilbert193

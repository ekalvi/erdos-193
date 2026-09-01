import Mathlib.NumberTheory.Padics.PadicVal.Basic

namespace Hilbert193

abbrev Vec2 := ℤ × ℤ

/-- The ordinary 2-adic order on a nonzero integer coordinate. -/
def coordVal (z : ℤ) : ℕ := padicValNat 2 z.natAbs

/-- The pair valuation from the Hilbert low-digit mismatch table.
Zero coordinates are treated as having infinite order by handling them separately. -/
def pairVal (u : Vec2) : ℕ :=
  if u.1 = 0 then
    if u.2 = 0 then 0 else 2 * coordVal u.2
  else if u.2 = 0 then
    2 * coordVal u.1
  else
    2 * min (coordVal u.1) (coordVal u.2) +
      if coordVal u.1 = coordVal u.2 then 1 else 0

@[simp] theorem pairVal_zero : pairVal (0, 0) = 0 := by simp [pairVal]
@[simp] theorem coordVal_neg (z : ℤ) : coordVal (-z) = coordVal z := by
  simp [coordVal]

@[simp] theorem pairVal_neg (u : Vec2) : pairVal (-u.1, -u.2) = pairVal u := by
  rcases u with ⟨x, y⟩
  by_cases hx : x = 0 <;> by_cases hy : y = 0 <;>
    simp [pairVal, hx, hy, coordVal_neg]

private theorem coordVal_mul_nat (k : ℕ) (z : ℤ) (hk : k ≠ 0) (hz : z ≠ 0) :
    coordVal ((k : ℤ) * z) = coordVal z + padicValNat 2 k := by
  simp only [coordVal, Int.natAbs_mul, Int.natAbs_natCast]
  rw [padicValNat.mul]
  · omega
  · exact hk
  · simpa using hz

/-- Multiplying a nonzero planar vector by `k` adds twice the 2-adic order of `k`. -/
theorem pairVal_nsmul (k : ℕ) (u : Vec2) (hk : k ≠ 0) (hu : u ≠ (0, 0)) :
    pairVal ((k : ℤ) * u.1, (k : ℤ) * u.2) = pairVal u + 2 * padicValNat 2 k := by
  rcases u with ⟨x, y⟩
  by_cases hx : x = 0
  · subst x
    have hy : y ≠ 0 := by
      intro hy
      apply hu
      simp [hy]
    simp [pairVal, hk, hy, coordVal_mul_nat k y hk hy, Nat.mul_add]
    <;> omega
  · by_cases hy : y = 0
    · subst y
      have hx' : x ≠ 0 := hx
      simp [pairVal, hk, hx', coordVal_mul_nat k x hk hx', Nat.mul_add]
      <;> omega
    · have hkz : (k : ℤ) ≠ 0 := by exact_mod_cast hk
      have hkx : (k : ℤ) * x ≠ 0 := mul_ne_zero hkz hx
      have hky : (k : ℤ) * y ≠ 0 := mul_ne_zero hkz hy
      simp only [pairVal, hx, hy, hkx, hky, if_false]
      rw [coordVal_mul_nat k x hk hx, coordVal_mul_nat k y hk hy]
      have hmin : min (coordVal x + padicValNat 2 k) (coordVal y + padicValNat 2 k) =
          min (coordVal x) (coordVal y) + padicValNat 2 k := by omega
      rw [hmin]
      by_cases hxy : coordVal x = coordVal y
      · simp [hxy, Nat.mul_add]
        <;> omega
      · have hxy' : coordVal x + padicValNat 2 k ≠ coordVal y + padicValNat 2 k := by omega
        simp [hxy, hxy', Nat.mul_add]
        <;> omega

theorem coordVal_eq_zero_of_not_two_dvd {z : ℤ} (hodd : ¬(2 : ℤ) ∣ z) :
    coordVal z = 0 := by
  unfold coordVal
  apply padicValNat.eq_zero_of_not_dvd
  intro hd
  apply hodd
  apply Int.dvd_natAbs.mp
  exact Int.natCast_dvd_natCast.mpr hd

theorem coordVal_ne_zero_of_two_dvd {z : ℤ} (hz : z ≠ 0) (heven : (2 : ℤ) ∣ z) :
    coordVal z ≠ 0 := by
  obtain ⟨k, hk⟩ := heven
  subst z
  have hk0 : k ≠ 0 := by
    intro h
    subst k
    simp at hz
  have hv : coordVal (2 * k) = coordVal k + padicValNat 2 2 := by
    simpa using coordVal_mul_nat 2 k (by decide) hk0
  rw [hv, padicValNat_base (by decide)]
  omega

theorem pairVal_odd_even {x y : ℤ} (hx : ¬(2 : ℤ) ∣ x) (hy : (2 : ℤ) ∣ y) :
    pairVal (x, y) = 0 := by
  have hx0 : x ≠ 0 := by
    intro h
    subst x
    exact hx (by simp)
  have hvx : coordVal x = 0 := coordVal_eq_zero_of_not_two_dvd hx
  by_cases hy0 : y = 0
  · simp [pairVal, hx0, hy0, hvx]
  · have hvy : coordVal y ≠ 0 := coordVal_ne_zero_of_two_dvd hy0 hy
    have hvy' : 0 ≠ coordVal y := Ne.symm hvy
    simp [pairVal, hx0, hy0, hvx, hvy']

theorem pairVal_even_odd {x y : ℤ} (hx : (2 : ℤ) ∣ x) (hy : ¬(2 : ℤ) ∣ y) :
    pairVal (x, y) = 0 := by
  have hy0 : y ≠ 0 := by
    intro h
    subst y
    exact hy (by simp)
  have hvy : coordVal y = 0 := coordVal_eq_zero_of_not_two_dvd hy
  by_cases hx0 : x = 0
  · simp [pairVal, hx0, hy0, hvy]
  · have hvx : coordVal x ≠ 0 := coordVal_ne_zero_of_two_dvd hx0 hx
    simp [pairVal, hx0, hy0, hvx, hvy]

theorem pairVal_odd_odd {x y : ℤ} (hx : ¬(2 : ℤ) ∣ x) (hy : ¬(2 : ℤ) ∣ y) :
    pairVal (x, y) = 1 := by
  have hx0 : x ≠ 0 := by
    intro h
    subst x
    exact hx (by simp)
  have hy0 : y ≠ 0 := by
    intro h
    subst y
    exact hy (by simp)
  have hvx : coordVal x = 0 := coordVal_eq_zero_of_not_two_dvd hx
  have hvy : coordVal y = 0 := coordVal_eq_zero_of_not_two_dvd hy
  simp [pairVal, hx0, hy0, hvx, hvy]

end Hilbert193

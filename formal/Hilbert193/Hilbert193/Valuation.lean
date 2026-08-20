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

end Hilbert193

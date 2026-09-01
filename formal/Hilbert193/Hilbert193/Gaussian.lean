import Mathlib.Data.Nat.BinaryRec
import Hilbert193.GaussianValuation

/-! Binary recursion and the same-state chord law for the Gaussian walk. -/

namespace Hilbert193

inductive Direction where
  | east | north | west | south
  deriving DecidableEq, Repr

namespace Direction

def rotate : Direction → Direction
  | east => north
  | north => west
  | west => south
  | south => east

@[simp] theorem rotate_injective : Function.Injective rotate := by
  intro a b h
  cases a <;> cases b <;> simp_all [rotate]

def vec : Direction → Vec2
  | east => (1, 0)
  | north => (0, 1)
  | west => (-1, 0)
  | south => (0, -1)

def label : Direction → ℕ
  | east => 0
  | north => 1
  | west => 2
  | south => 3

def tag : Direction → Vec2
  | east => (0, 0)
  | north => (0, 1)
  | west => (-1, 1)
  | south => (-1, 0)

@[simp] theorem label_le_three (d : Direction) : label d ≤ 3 := by
  cases d <;> decide

@[simp] theorem vec_ne_zero (d : Direction) : vec d ≠ (0, 0) := by
  cases d <;> decide

@[simp] theorem vec_rotate (d : Direction) : vec (rotate d) = (- (vec d).2, (vec d).1) := by
  cases d <;> decide

end Direction


@[simp] theorem mulOnePlusI_zero : mulOnePlusI (0, 0) = (0, 0) := rfl

@[simp] theorem mulOnePlusI_add (p q : Vec2) :
    mulOnePlusI (addVec p q) = addVec (mulOnePlusI p) (mulOnePlusI q) := by
  apply Prod.ext <;> simp [mulOnePlusI, addVec] <;> ring

@[simp] theorem mulOnePlusI_direction (d : Direction) :
    mulOnePlusI (Direction.vec d) =
      addVec (Direction.vec d) (Direction.vec (Direction.rotate d)) := by
  cases d <;> decide

private def gaussianStep (b : Bool) (_n : ℕ) (data : Direction × Vec2) : Direction × Vec2 :=
  let d := data.1
  let z := data.2
  if b then
    (d.rotate, addVec (mulOnePlusI z) d.vec)
  else
    (d, mulOnePlusI z)

def gaussianData (n : ℕ) : Direction × Vec2 :=
  Nat.binaryRec (.east, (0, 0)) gaussianStep n

def gaussianState (n : ℕ) : Direction := (gaussianData n).1

def gaussianPlanar (n : ℕ) : Vec2 := (gaussianData n).2

def gaussianUnit (n : ℕ) : Vec2 := (gaussianState n).vec

@[simp] theorem gaussianData_zero : gaussianData 0 = (.east, (0, 0)) := rfl

@[simp] theorem gaussianData_bit (b : Bool) (n : ℕ) :
    gaussianData (Nat.bit b n) = gaussianStep b n (gaussianData n) := by
  apply Nat.binaryRec_eq
  left
  rfl

@[simp] theorem gaussianState_two_mul (n : ℕ) : gaussianState (2 * n) = gaussianState n := by
  simpa [gaussianState, gaussianStep] using congrArg Prod.fst (gaussianData_bit false n)

@[simp] theorem gaussianState_two_mul_add_one (n : ℕ) :
    gaussianState (2 * n + 1) = (gaussianState n).rotate := by
  simpa [gaussianState, gaussianStep] using congrArg Prod.fst (gaussianData_bit true n)

@[simp] theorem gaussianPlanar_two_mul (n : ℕ) :
    gaussianPlanar (2 * n) = mulOnePlusI (gaussianPlanar n) := by
  simpa [gaussianPlanar, gaussianStep] using congrArg Prod.snd (gaussianData_bit false n)

@[simp] theorem gaussianPlanar_two_mul_add_one (n : ℕ) :
    gaussianPlanar (2 * n + 1) =
      addVec (mulOnePlusI (gaussianPlanar n)) (gaussianUnit n) := by
  simpa [gaussianPlanar, gaussianUnit, gaussianState, gaussianStep] using
    congrArg Prod.snd (gaussianData_bit true n)

@[simp] theorem gaussianUnit_two_mul (n : ℕ) : gaussianUnit (2 * n) = gaussianUnit n := by
  simp [gaussianUnit]

@[simp] theorem gaussianUnit_two_mul_add_one (n : ℕ) :
    gaussianUnit (2 * n + 1) = (-(gaussianUnit n).2, (gaussianUnit n).1) := by
  simp [gaussianUnit, Direction.vec_rotate]

@[simp] theorem gaussianPlanar_succ (n : ℕ) :
    gaussianPlanar (n + 1) = addVec (gaussianPlanar n) (gaussianUnit n) := by
  induction n using Nat.binaryRec with
  | zero => decide
  | bit b n ih =>
      cases b
      · simp [addVec]
      · rw [Nat.bit_true_apply]
        have heq : 2 * n + 1 + 1 = 2 * (n + 1) := by omega
        rw [heq, gaussianPlanar_two_mul, ih, mulOnePlusI_add,
          gaussianPlanar_two_mul_add_one, gaussianUnit_two_mul_add_one]
        have hu := mulOnePlusI_direction (gaussianState n)
        rw [Direction.vec_rotate] at hu
        change mulOnePlusI (gaussianUnit n) =
          addVec (gaussianUnit n) (-(gaussianUnit n).2, (gaussianUnit n).1) at hu
        rw [hu]
        apply Prod.ext <;> simp [addVec] <;> ring


def subVec (p q : Vec2) : Vec2 := (p.1 - q.1, p.2 - q.2)

@[simp] theorem gaussianUnit_sum_parity (n : ℕ) :
    (2 : ℤ) ∣ (gaussianUnit n).1 + (gaussianUnit n).2 - 1 := by
  unfold gaussianUnit
  cases gaussianState n <;> simp [Direction.vec]

theorem gaussianPlanar_sum_parity (n : ℕ) :
    (2 : ℤ) ∣ (gaussianPlanar n).1 + (gaussianPlanar n).2 - n := by
  induction n with
  | zero => simp [gaussianPlanar]
  | succ n ih =>
      obtain ⟨a, ha⟩ := ih
      obtain ⟨b, hb⟩ := gaussianUnit_sum_parity n
      refine ⟨a + b, ?_⟩
      rw [gaussianPlanar_succ]
      simp only [addVec]
      omega

theorem subVec_sum_odd_of_gap_odd {m n : ℕ}
    (hgap : ¬(2 : ℤ) ∣ (n : ℤ) - m) :
    ¬(2 : ℤ) ∣ (subVec (gaussianPlanar n) (gaussianPlanar m)).1 +
      (subVec (gaussianPlanar n) (gaussianPlanar m)).2 := by
  intro hsum
  apply hgap
  obtain ⟨a, ha⟩ := gaussianPlanar_sum_parity n
  obtain ⟨b, hb⟩ := gaussianPlanar_sum_parity m
  obtain ⟨c, hc⟩ := hsum
  refine ⟨c - a + b, ?_⟩
  simp only [subVec] at hc
  omega


@[simp] theorem mulOnePlusI_sub (p q : Vec2) :
    subVec (mulOnePlusI p) (mulOnePlusI q) = mulOnePlusI (subVec p q) := by
  apply Prod.ext <;> simp [subVec, mulOnePlusI] <;> ring

theorem mulOnePlusI_ne_zero {u : Vec2} (hu : u ≠ (0, 0)) :
    mulOnePlusI u ≠ (0, 0) := by
  intro h
  apply hu
  apply Prod.ext
  · have hx := congrArg Prod.fst h
    have hy := congrArg Prod.snd h
    simp [mulOnePlusI] at hx hy
    omega
  · have hx := congrArg Prod.fst h
    have hy := congrArg Prod.snd h
    simp [mulOnePlusI] at hx hy
    omega

private theorem padicValNat_two_mul (d : ℕ) (hd : d ≠ 0) :
    padicValNat 2 (2 * d) = padicValNat 2 d + 1 := by
  rw [padicValNat.mul (by decide) hd, padicValNat_base (by decide)]
  omega

/-- Stijn Cambie's halving law, strengthened with nonvanishing of the chord. -/
private theorem gaussian_same_state_pair_law_aux {m n : ℕ} (hmn : m < n)
    (hstate : gaussianState m = gaussianState n) :
    pairVal (subVec (gaussianPlanar n) (gaussianPlanar m)) =
        padicValNat 2 (n - m) ∧
      subVec (gaussianPlanar n) (gaussianPlanar m) ≠ (0, 0) := by
  induction n using Nat.strong_induction_on generalizing m with
  | h n ih =>
      obtain ⟨a, rfl | rfl⟩ := Nat.even_or_odd' m
      · obtain ⟨b, rfl | rfl⟩ := Nat.even_or_odd' n
        · have hab : a < b := by omega
          have hstate' : gaussianState a = gaussianState b := by simpa using hstate
          have hp := ih b (by omega) hab hstate'
          constructor
          · rw [gaussianPlanar_two_mul, gaussianPlanar_two_mul, mulOnePlusI_sub,
              pairVal_mulOnePlusI hp.2,
              show 2 * b - 2 * a = 2 * (b - a) by omega,
              padicValNat_two_mul (b - a) (by omega), hp.1]
          · rw [gaussianPlanar_two_mul, gaussianPlanar_two_mul, mulOnePlusI_sub]
            exact mulOnePlusI_ne_zero hp.2
        · have hodd := subVec_sum_odd_of_gap_odd (m := 2 * a) (n := 2 * b + 1) (by
            intro hd
            obtain ⟨k, hk⟩ := hd
            push_cast at hk
            omega)
          constructor
          · rw [pairVal_eq_zero_of_sum_not_two_dvd hodd]
            refine (padicValNat.eq_zero_of_not_dvd ?_).symm
            omega
          · intro hz
            have hsumzero := congrArg (fun p : Vec2 => p.1 + p.2) hz
            apply hodd
            rw [hsumzero]
            simp
      · obtain ⟨b, rfl | rfl⟩ := Nat.even_or_odd' n
        · have hodd := subVec_sum_odd_of_gap_odd (m := 2 * a + 1) (n := 2 * b) (by
            intro hd
            obtain ⟨k, hk⟩ := hd
            push_cast at hk
            omega)
          constructor
          · rw [pairVal_eq_zero_of_sum_not_two_dvd hodd]
            refine (padicValNat.eq_zero_of_not_dvd ?_).symm
            omega
          · intro hz
            have hsumzero := congrArg (fun p : Vec2 => p.1 + p.2) hz
            apply hodd
            rw [hsumzero]
            simp
        · have hab : a < b := by omega
          have hstate' : gaussianState a = gaussianState b := by
            apply Direction.rotate_injective
            simpa using hstate
          have hp := ih b (by omega) hab hstate'
          have hunit : gaussianUnit a = gaussianUnit b := by simp [gaussianUnit, hstate']
          have hchord :
              subVec
                  (addVec (mulOnePlusI (gaussianPlanar b)) (gaussianUnit b))
                  (addVec (mulOnePlusI (gaussianPlanar a)) (gaussianUnit a)) =
                mulOnePlusI (subVec (gaussianPlanar b) (gaussianPlanar a)) := by
            rw [hunit]
            apply Prod.ext <;> simp [subVec, addVec, mulOnePlusI] <;> ring
          constructor
          · rw [gaussianPlanar_two_mul_add_one, gaussianPlanar_two_mul_add_one,
              hchord, pairVal_mulOnePlusI hp.2,
              show (2 * b + 1) - (2 * a + 1) = 2 * (b - a) by omega,
              padicValNat_two_mul (b - a) (by omega), hp.1]
          · rw [gaussianPlanar_two_mul_add_one, gaussianPlanar_two_mul_add_one,
              hchord]
            exact mulOnePlusI_ne_zero hp.2

/-- Equal Gaussian direction states give the exact two-adic chord law. -/
theorem gaussian_same_state_pair_law {m n : ℕ} (hmn : m < n)
    (hstate : gaussianState m = gaussianState n) :
    pairVal (subVec (gaussianPlanar n) (gaussianPlanar m)) =
      padicValNat 2 (n - m) :=
  (gaussian_same_state_pair_law_aux hmn hstate).1

theorem gaussianPlanar_ne_of_same_state {m n : ℕ} (hmn : m < n)
    (hstate : gaussianState m = gaussianState n) :
    gaussianPlanar m ≠ gaussianPlanar n := by
  intro h
  apply (gaussian_same_state_pair_law_aux hmn hstate).2
  simp [subVec, h]

end Hilbert193

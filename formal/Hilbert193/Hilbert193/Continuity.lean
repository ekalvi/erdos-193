import Hilbert193.Construction

/-! The sixteen-state-pair step menu and final Erdős Problem 193 theorem. -/

namespace Hilbert193


def displacement (p q : Point3) : Point3 where
  x := q.x - p.x
  y := q.y - p.y
  z := q.z - p.z

/-- The step determined by the current and next Gaussian directions. -/
def gaussianStepVector (p q : Direction) : Point3 where
  x := 2 * p.vec.1 + q.tag.1 - p.tag.1
  y := 2 * p.vec.2 + q.tag.2 - p.tag.2
  z := 4 + q.label - p.label

def Direction.toFin : Direction → Fin 4
  | .east => 0
  | .north => 1
  | .west => 2
  | .south => 3

def directionOfFin (i : Fin 4) : Direction :=
  match i.1 with
  | 0 => .east
  | 1 => .north
  | 2 => .west
  | _ => .south

@[simp] theorem directionOfFin_toFin (d : Direction) :
    directionOfFin d.toFin = d := by cases d <;> rfl

/-- The fixed menu indexed by the sixteen ordered pairs of direction states. -/
def finiteStepMenu : Set Point3 :=
  Set.range fun pq : Fin 4 × Fin 4 =>
    gaussianStepVector (directionOfFin pq.1) (directionOfFin pq.2)

theorem finiteStepMenu_finite : finiteStepMenu.Finite := Set.finite_range _

theorem gaussianStepVector_bounds (p q : Direction) :
    -2 ≤ (gaussianStepVector p q).x ∧ (gaussianStepVector p q).x ≤ 2 ∧
    -2 ≤ (gaussianStepVector p q).y ∧ (gaussianStepVector p q).y ≤ 2 ∧
    1 ≤ (gaussianStepVector p q).z ∧ (gaussianStepVector p q).z ≤ 7 := by
  cases p <;> cases q <;>
    norm_num [gaussianStepVector, Direction.vec, Direction.tag, Direction.label]

/-- Each successive displacement is one of the sixteen state-pair vectors. -/
theorem taggedLift_step_mem (n : ℕ) :
    displacement (taggedLift n) (taggedLift (n + 1)) ∈ finiteStepMenu := by
  refine ⟨((gaussianState n).toFin, (gaussianState (n + 1)).toFin), ?_⟩
  apply Point3.ext
  · simp [displacement, taggedLift, taggedPlanar, gaussianStepVector,
      gaussianPlanar_succ, addVec, gaussianUnit]
    ring
  · simp [displacement, taggedLift, taggedPlanar, gaussianStepVector,
      gaussianPlanar_succ, addVec, gaussianUnit]
    ring
  · simp [displacement, taggedLift, taggedHeight, gaussianStepVector]
    ring

/-- Unconditional finite-step, no-three-in-line walk in `ℤ³`. -/
theorem erdos193_unconditional :
    ∃ (S : Set Point3) (P : ℕ → Point3),
      S.Finite ∧
      (∀ n, displacement (P n) (P (n + 1)) ∈ S) ∧
      (∀ ⦃i j k⦄, i < j → j < k → ¬ OrderedCollinear (P i) (P j) (P k)) := by
  refine ⟨finiteStepMenu, taggedLift, finiteStepMenu_finite, taggedLift_step_mem, ?_⟩
  intro i j k hij hjk
  exact taggedLift_no_three hij hjk

end Hilbert193

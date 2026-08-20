import Mathlib

namespace Hilbert193

inductive Digit where
  | d0 | d1 | d2 | d3
  deriving DecidableEq, Repr

inductive Bit where
  | zero | one
  deriving DecidableEq, Repr

namespace Bit

def xor : Bit → Bit → Bit
  | zero, b => b
  | one, zero => one
  | one, one => zero

@[simp] theorem zero_xor (b : Bit) : xor zero b = b := by cases b <;> rfl
@[simp] theorem one_xor_zero : xor one zero = one := rfl
@[simp] theorem one_xor_one : xor one one = zero := rfl
@[simp] theorem xor_self (b : Bit) : xor b b = zero := by cases b <;> rfl
@[simp] theorem xor_zero (b : Bit) : xor b zero = b := by cases b <;> rfl
@[simp] theorem xor_assoc (a b c : Bit) : xor (xor a b) c = xor a (xor b c) := by
  cases a <;> cases b <;> cases c <;> rfl
@[simp] theorem xor_comm (a b : Bit) : xor a b = xor b a := by cases a <;> cases b <;> rfl

def toNat : Bit → ℕ
  | zero => 0
  | one => 1

end Bit

abbrev BitPair := Bit × Bit

/-- A square symmetry: optional coordinate swap, then coordinate complements. -/
structure Orient where
  swap : Bit
  bx : Bit
  cy : Bit
  deriving DecidableEq, Repr

namespace Orient

def choose (s a b : Bit) : Bit := if s = Bit.zero then a else b

def act (g : Orient) (p : BitPair) : BitPair :=
  (Bit.xor (choose g.swap p.1 p.2) g.bx,
   Bit.xor (choose g.swap p.2 p.1) g.cy)

/-- `compose g h` means apply `h`, then apply `g`. -/
def compose (g h : Orient) : Orient where
  swap := Bit.xor g.swap h.swap
  bx := Bit.xor (choose g.swap h.bx h.cy) g.bx
  cy := Bit.xor (choose g.swap h.cy h.bx) g.cy

abbrev I : Orient := ⟨.zero, .zero, .zero⟩
abbrev X : Orient := ⟨.zero, .one, .zero⟩
abbrev Y : Orient := ⟨.zero, .zero, .one⟩
abbrev C : Orient := ⟨.zero, .one, .one⟩
abbrev S : Orient := ⟨.one, .zero, .zero⟩
abbrev R : Orient := ⟨.one, .one, .zero⟩
abbrev L : Orient := ⟨.one, .zero, .one⟩
abbrev T : Orient := ⟨.one, .one, .one⟩

@[simp] theorem act_I (p : BitPair) : act I p = p := by rcases p with ⟨x,y⟩; cases x <;> cases y <;> rfl
@[simp] theorem compose_I_left (g : Orient) : compose I g = g := by rcases g with ⟨s,x,y⟩; cases s <;> cases x <;> cases y <;> rfl
@[simp] theorem compose_I_right (g : Orient) : compose g I = g := by rcases g with ⟨s,x,y⟩; cases s <;> cases x <;> cases y <;> rfl

theorem act_compose (g h : Orient) (p : BitPair) : act (compose g h) p = act g (act h p) := by
  rcases g with ⟨gs,gx,gy⟩
  rcases h with ⟨hs,hx,hy⟩
  rcases p with ⟨x,y⟩
  cases gs <;> cases gx <;> cases gy <;> cases hs <;> cases hx <;> cases hy <;>
    cases x <;> cases y <;> rfl

theorem compose_assoc (g h k : Orient) : compose (compose g h) k = compose g (compose h k) := by
  rcases g with ⟨gs,gx,gy⟩
  rcases h with ⟨hs,hx,hy⟩
  rcases k with ⟨ks,kx,ky⟩
  cases gs <;> cases gx <;> cases gy <;> cases hs <;> cases hx <;> cases hy <;>
    cases ks <;> cases kx <;> cases ky <;> rfl

end Orient

open Orient

def child : Digit → BitPair
  | .d0 => (.zero, .zero)
  | .d1 => (.zero, .one)
  | .d2 => (.one, .one)
  | .d3 => (.one, .zero)

def refinement : Digit → Orient
  | .d0 => S
  | .d1 => I
  | .d2 => I
  | .d3 => T

def emit (state : Orient) (d : Digit) : BitPair := state.act (child d)
def next (state : Orient) (d : Digit) : Orient := state.compose (refinement d)

/-- One complete literal transducer row, ordered by digits 0,1,2,3. -/
def row (state : Orient) : List (BitPair × Orient) :=
  [(.d0),(.d1),(.d2),(.d3)].map fun d => (emit state d, next state d)

/-- The exact eight rows printed in the research memo. -/
theorem complete_table :
    row I = [((.zero,.zero),S),((.zero,.one),I),((.one,.one),I),((.one,.zero),T)] ∧
    row X = [((.one,.zero),R),((.one,.one),X),((.zero,.one),X),((.zero,.zero),L)] ∧
    row Y = [((.zero,.one),L),((.zero,.zero),Y),((.one,.zero),Y),((.one,.one),R)] ∧
    row C = [((.one,.one),T),((.one,.zero),C),((.zero,.zero),C),((.zero,.one),S)] ∧
    row S = [((.zero,.zero),I),((.one,.zero),S),((.one,.one),S),((.zero,.one),C)] ∧
    row R = [((.one,.zero),X),((.zero,.zero),R),((.zero,.one),R),((.one,.one),Y)] ∧
    row L = [((.zero,.one),Y),((.one,.one),L),((.one,.zero),L),((.zero,.zero),X)] ∧
    row T = [((.one,.one),C),((.zero,.one),T),((.zero,.zero),T),((.one,.zero),I)] := by
  decide

@[simp] theorem refinement_involution (d : Digit) :
    (refinement d).compose (refinement d) = I := by cases d <;> decide

@[simp] theorem refinement_fixes_child (d : Digit) :
    (refinement d).act (child d) = child d := by cases d <;> decide

/-- Reverse one labeled transition exactly. -/
theorem reverse_transition (g h : Orient) (d : Digit) (hh : next g d = h) :
    g = h.compose (refinement d) := by
  subst h
  symm
  calc
    (next g d).compose (refinement d) =
        (g.compose (refinement d)).compose (refinement d) := rfl
    _ = g.compose ((refinement d).compose (refinement d)) := Orient.compose_assoc _ _ _
    _ = g := by rw [refinement_involution, Orient.compose_I_right]

/-- The emitted bits can be read from the outgoing orientation. -/
theorem backward_emit (g : Orient) (d : Digit) : emit g d = emit (next g d) d := by
  simp only [emit, next, Orient.act_compose, refinement_fixes_child]

/-- Forward transduction of a most-significant-first digit word. -/
def run : Orient → List Digit → List BitPair × Orient
  | s, [] => ([], s)
  | s, d :: ds =>
      let tail := run (next s d) ds
      (emit s d :: tail.1, tail.2)

def terminal (ds : List Digit) : Orient := (run I ds).2

def bitValue (bits : List Bit) : ℕ := bits.foldl (fun n b => 2*n + b.toNat) 0

def coordinate (ds : List Digit) : ℕ × ℕ :=
  let bits := (run I ds).1
  (bitValue (bits.map Prod.fst), bitValue (bits.map Prod.snd))

@[simp] theorem run_nil (s : Orient) : run s [] = ([],s) := rfl

/-- Two leading zero digits add two zero output bits and restore the initial state. -/
theorem even_zero_padding (ds : List Digit) :
    run I (.d0 :: .d0 :: ds) =
      let tail := run I ds
      ((.zero,.zero) :: (.zero,.zero) :: tail.1, tail.2) := by
  have hSS : S.compose S = I := by decide
  simp [run, next, emit, child, refinement, Orient.act, Orient.choose, hSS]

/-- Counts of digits 0 and 3 modulo two, represented as a reachable orientation. -/
def parityState (ds : List Digit) : Orient :=
  ds.foldl (fun s d => next s d) I

theorem run_terminal (s : Orient) (ds : List Digit) :
    (run s ds).2 = ds.foldl (fun state d => next state d) s := by
  induction ds generalizing s with
  | nil => rfl
  | cons d ds ih => simp [run, ih]

/-- Contribution of one digit to the two terminal parities `(number of 0s, number of 3s)`. -/
def digitParity : Digit → BitPair
  | .d0 => (.one, .zero)
  | .d1 => (.zero, .zero)
  | .d2 => (.zero, .zero)
  | .d3 => (.zero, .one)

def xorPair (a b : BitPair) : BitPair := (Bit.xor a.1 b.1, Bit.xor a.2 b.2)

def wordParity : List Digit → BitPair
  | [] => (.zero, .zero)
  | d :: ds => xorPair (digitParity d) (wordParity ds)

def orientOfParity : BitPair → Orient
  | (.zero, .zero) => I
  | (.one, .zero) => S
  | (.zero, .one) => T
  | (.one, .one) => C

theorem refinement_eq_orientParity (d : Digit) :
    refinement d = orientOfParity (digitParity d) := by cases d <;> rfl

theorem orientOfParity_xor (a b : BitPair) :
    orientOfParity (xorPair a b) = (orientOfParity a).compose (orientOfParity b) := by
  rcases a with ⟨a₀,a₃⟩
  rcases b with ⟨b₀,b₃⟩
  cases a₀ <;> cases a₃ <;> cases b₀ <;> cases b₃ <;> decide

theorem run_state_parity (s : Orient) (ds : List Digit) :
    (run s ds).2 = s.compose (orientOfParity (wordParity ds)) := by
  induction ds generalizing s with
  | nil => simp [run, wordParity, orientOfParity]
  | cons d ds ih =>
      rw [show (run s (d :: ds)).2 = (run (next s d) ds).2 by rfl, ih]
      simp only [next, refinement_eq_orientParity, wordParity, orientOfParity_xor]
      rw [Orient.compose_assoc]

/-- The terminal state is exactly the two parities of complete digit counts. -/
theorem terminal_statistic (ds : List Digit) :
    terminal ds = orientOfParity (wordParity ds) := by
  rw [terminal, run_state_parity, Orient.compose_I_left]

theorem wordParity_append (a b : List Digit) :
    wordParity (a ++ b) = xorPair (wordParity a) (wordParity b) := by
  induction a with
  | nil =>
      change wordParity b = xorPair (.zero,.zero) (wordParity b)
      generalize wordParity b = p
      rcases p with ⟨x,y⟩
      cases x <;> cases y <;> decide
  | cons d ds ih =>
      simp only [List.cons_append, wordParity, ih]
      rcases digitParity d with ⟨a₁,a₂⟩
      rcases wordParity ds with ⟨b₁,b₂⟩
      rcases wordParity b with ⟨c₁,c₂⟩
      cases a₁ <;> cases a₂ <;> cases b₁ <;> cases b₂ <;>
        cases c₁ <;> cases c₂ <;> decide

/-- Two low base-4 digits that cancel a prescribed terminal parity. -/
def steeringDigits : BitPair → List Digit
  | (.zero, .zero) => [.d1, .d1]
  | (.one, .zero) => [.d0, .d1]
  | (.zero, .one) => [.d3, .d1]
  | (.one, .one) => [.d0, .d3]

/-- Appending the two steering digits sends every word to terminal state `I`. -/
theorem terminal_steered (ds : List Digit) :
    terminal (ds ++ steeringDigits (wordParity ds)) = I := by
  rw [terminal_statistic, wordParity_append]
  generalize hp : wordParity ds = p
  rcases p with ⟨p₀,p₃⟩
  cases p₀ <;> cases p₃ <;> decide

@[simp] theorem terminal_eq_parityState (ds : List Digit) : terminal ds = parityState ds := by
  simp [terminal, parityState, run_terminal]

end Hilbert193

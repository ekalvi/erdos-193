import Hilbert193.Construction

namespace Hilbert193

open Orient


/-- Most-significant-first evaluation of a base-4 word. -/
def indexMSB : List Digit → ℕ
  | [] => 0
  | d :: ds => d.toNat * 4 ^ ds.length + indexMSB ds

/-- Most-significant-first coordinate evaluation, generalized to an incoming orientation. -/
def coordinateMSB : Orient → List Digit → ℕ × ℕ
  | _, [] => (0, 0)
  | s, d :: ds =>
      let b := emit s d
      let q := coordinateMSB (next s d) ds
      (b.1.toNat * 2 ^ ds.length + q.1,
        b.2.toNat * 2 ^ ds.length + q.2)

/-- Apply a square orientation to coordinates in `[0,m]²`. -/
def Orient.actNat (s : Orient) (m : ℕ) (p : ℕ × ℕ) : ℕ × ℕ :=
  let x := if s.swap = .zero then p.1 else p.2
  let y := if s.swap = .zero then p.2 else p.1
  (if s.bx = .zero then x else m - x,
    if s.cy = .zero then y else m - y)

private def zeroWord (n : ℕ) : List Digit := List.replicate n .d0
private def threeWord (n : ℕ) : List Digit := List.replicate n .d3

@[simp] private theorem zeroWord_succ (n : ℕ) :
    zeroWord (n + 1) = .d0 :: zeroWord n := by
  simpa [zeroWord] using (List.replicate_succ (a := Digit.d0) (n := n))

@[simp] private theorem threeWord_succ (n : ℕ) :
    threeWord (n + 1) = .d3 :: threeWord n := by
  simpa [threeWord] using (List.replicate_succ (a := Digit.d3) (n := n))

@[simp] private theorem zeroWord_length (n : ℕ) : (zeroWord n).length = n := by
  simp [zeroWord]

@[simp] private theorem threeWord_length (n : ℕ) : (threeWord n).length = n := by
  simp [threeWord]

private theorem coordinateMSB_endpoints (s : Orient) (n : ℕ) :
    coordinateMSB s (zeroWord n) = s.actNat (2 ^ n - 1) (0, 0) ∧
    coordinateMSB s (threeWord n) = s.actNat (2 ^ n - 1) (2 ^ n - 1, 0) := by
  induction n generalizing s with
  | zero =>
      rcases s with ⟨sw, bx, cy⟩
      cases sw <;> cases bx <;> cases cy <;>
        decide
  | succ n ih =>
      rcases s with ⟨sw, bx, cy⟩
      cases sw <;> cases bx <;> cases cy <;>
        simp only [zeroWord_succ, threeWord_succ, coordinateMSB,
          zeroWord_length, threeWord_length, Bit.toNat, ih] <;>
        simp [Orient.actNat, emit, next, child, refinement, Orient.act,
          Orient.compose, Orient.choose, Nat.pow_succ] <;>
        omega

/-- Lexicographic base-4 successor on fixed-length words. -/
inductive WordSucc : List Digit → List Digit → Prop
  | tail (d : Digit) {a b : List Digit} (h : WordSucc a b) : WordSucc (d :: a) (d :: b)
  | d01 (n : ℕ) : WordSucc (.d0 :: threeWord n) (.d1 :: zeroWord n)
  | d12 (n : ℕ) : WordSucc (.d1 :: threeWord n) (.d2 :: zeroWord n)
  | d23 (n : ℕ) : WordSucc (.d2 :: threeWord n) (.d3 :: zeroWord n)

theorem WordSucc.length_eq {a b : List Digit} (h : WordSucc a b) :
    a.length = b.length := by
  induction h with
  | tail d h ih => simp [ih]
  | d01 n => simp [zeroWord, threeWord]
  | d12 n => simp [zeroWord, threeWord]
  | d23 n => simp [zeroWord, threeWord]

private theorem indexMSB_lt_pow (ds : List Digit) :
    indexMSB ds < 4 ^ ds.length := by
  induction ds with
  | nil => simp [indexMSB]
  | cons d ds ih =>
      cases d <;> simp [indexMSB, Digit.toNat, Nat.pow_succ] at ih ⊢ <;> omega

private theorem indexMSB_eq_zero (ds : List Digit) (h : indexMSB ds = 0) :
    ds = zeroWord ds.length := by
  induction ds with
  | nil => rfl
  | cons d ds ih =>
      cases d <;> simp [indexMSB, Digit.toNat] at h
      · change Digit.d0 :: ds = Digit.d0 :: zeroWord ds.length
        congr
        exact ih h

private theorem indexMSB_eq_max (ds : List Digit)
    (h : indexMSB ds = 4 ^ ds.length - 1) :
    ds = threeWord ds.length := by
  induction ds with
  | nil => rfl
  | cons d ds ih =>
      have ht := indexMSB_lt_pow ds
      cases d <;>
        simp [indexMSB, Digit.toNat, Nat.pow_succ] at h
      all_goals
        try omega
      change Digit.d3 :: ds = Digit.d3 :: threeWord ds.length
      congr
      exact ih (by omega)

private theorem carry_bounds {A B p : ℕ} (hp : 0 < p) (hA : A < p) (hB : B < p)
    (h : A + 1 = p + B) : A = p - 1 ∧ B = 0 := by
  omega

/-- Numeric succession characterizes lexicographic base-4 word succession at
fixed length. -/
theorem WordSucc.of_index {a b : List Digit} (hlen : a.length = b.length)
    (hindex : indexMSB a + 1 = indexMSB b) : WordSucc a b := by
  induction a generalizing b with
  | nil =>
      cases b <;> simp_all [indexMSB]
  | cons d ds ih =>
      cases b with
      | nil => simp at hlen
      | cons e es =>
          have hlen' : ds.length = es.length := by simpa using hlen
          have ha := indexMSB_lt_pow ds
          have hb := indexMSB_lt_pow es
          simp only [indexMSB, List.length_cons] at hindex
          rw [hlen'] at hindex ha
          cases d <;> cases e
          all_goals simp only [Digit.toNat] at hindex
          · exact .tail .d0 (ih hlen' (by omega))
          · have hc : indexMSB ds + 1 = 4 ^ es.length + indexMSB es := by omega
            obtain ⟨hmax, hzero⟩ := carry_bounds (by positivity) ha hb hc
            have hmax' : indexMSB ds = 4 ^ ds.length - 1 := by simpa [hlen'] using hmax
            rw [indexMSB_eq_max ds hmax', indexMSB_eq_zero es hzero]
            simpa [hlen'] using WordSucc.d01 ds.length
          · omega
          · omega
          · omega
          · exact .tail .d1 (ih hlen' (by omega))
          · have hc : indexMSB ds + 1 = 4 ^ es.length + indexMSB es := by omega
            obtain ⟨hmax, hzero⟩ := carry_bounds (by positivity) ha hb hc
            have hmax' : indexMSB ds = 4 ^ ds.length - 1 := by simpa [hlen'] using hmax
            rw [indexMSB_eq_max ds hmax', indexMSB_eq_zero es hzero]
            simpa [hlen'] using WordSucc.d12 ds.length
          · omega
          · omega
          · omega
          · exact .tail .d2 (ih hlen' (by omega))
          · have hc : indexMSB ds + 1 = 4 ^ es.length + indexMSB es := by omega
            obtain ⟨hmax, hzero⟩ := carry_bounds (by positivity) ha hb hc
            have hmax' : indexMSB ds = 4 ^ ds.length - 1 := by simpa [hlen'] using hmax
            rw [indexMSB_eq_max ds hmax', indexMSB_eq_zero es hzero]
            simpa [hlen'] using WordSucc.d23 ds.length
          · omega
          · omega
          · omega
          · exact .tail .d3 (ih hlen' (by omega))

@[simp] theorem indexMSB_append (a b : List Digit) :
    indexMSB (a ++ b) = indexMSB a * 4 ^ b.length + indexMSB b := by
  induction a with
  | nil => simp [indexMSB]
  | cons d ds ih =>
      simp only [List.cons_append, indexMSB, List.length_append, List.length_cons, ih]
      ring

@[simp] theorem indexMSB_reverse (ds : List Digit) :
    indexMSB ds.reverse = indexLSB ds := by
  induction ds with
  | nil => rfl
  | cons d ds ih =>
      rw [List.reverse_cons, indexMSB_append, ih]
      simp [indexMSB, indexLSB]
      ring

theorem indexLSB_injective_of_length {a b : List Digit}
    (hlen : a.length = b.length) (hindex : indexLSB a = indexLSB b) : a = b := by
  induction a generalizing b with
  | nil => cases b <;> simp_all
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

private theorem indexLSB_map_digitOfNat_fixed (ns : List ℕ)
    (hsmall : ∀ n ∈ ns, n < 4) :
    indexLSB (ns.map digitOfNat) = Nat.ofDigits 4 ns := by
  induction ns with
  | nil => rfl
  | cons n ns ih =>
      simp only [List.map_cons, indexLSB, Nat.ofDigits]
      rw [Digit.toNat_digitOfNat (hsmall n (by simp))]
      congr 1
      exact congrArg (fun z => 4 * z) (ih (fun x hx => hsmall x (by simp [hx])))

def fixedWord (k n : ℕ) : List Digit :=
  (Nat.digitsAppend 4 k n).map digitOfNat

theorem fixedWord_length {k n : ℕ} (hn : n < 4 ^ k) :
    (fixedWord k n).length = k := by
  simp [fixedWord, Nat.length_digitsAppend (by omega) k hn]

@[simp] theorem fixedWord_index {k n : ℕ} (hn : n < 4 ^ k) :
    indexLSB (fixedWord k n) = n := by
  have hsmall : ∀ d ∈ Nat.digitsAppend 4 k n, d < 4 :=
    fun d hd => Nat.lt_of_mem_digitsAppend (by omega) k d hd
  unfold fixedWord
  rw [indexLSB_map_digitOfNat_fixed _ hsmall]
  exact (Nat.setInvOn_digitsAppend_ofDigits (b := 4) (by omega) k).2 hn

def planarDist (p q : ℕ × ℕ) : ℕ :=
  Int.natAbs ((q.1 : ℤ) - p.1) + Int.natAbs ((q.2 : ℤ) - p.2)

theorem planarDist_triangle (p q r : ℕ × ℕ) :
    planarDist p r ≤ planarDist p q + planarDist q r := by
  have hx := Int.natAbs_add_le ((r.1 : ℤ) - q.1) ((q.1 : ℤ) - p.1)
  have hy := Int.natAbs_add_le ((r.2 : ℤ) - q.2) ((q.2 : ℤ) - p.2)
  have hx' : Int.natAbs ((r.1 : ℤ) - p.1) ≤
      Int.natAbs ((r.1 : ℤ) - q.1) + Int.natAbs ((q.1 : ℤ) - p.1) := by
    convert hx using 1 <;> ring
  have hy' : Int.natAbs ((r.2 : ℤ) - p.2) ≤
      Int.natAbs ((r.2 : ℤ) - q.2) + Int.natAbs ((q.2 : ℤ) - p.2) := by
    convert hy using 1 <;> ring
  unfold planarDist
  omega

def fixedPoint (k n : ℕ) : ℕ × ℕ :=
  coordinateMSB I (fixedWord k n).reverse

/-- Consecutive fixed-order Hilbert words map to unit lattice neighbors. -/
theorem coordinateMSB_wordSucc {a b : List Digit} (h : WordSucc a b) (s : Orient) :
    Int.natAbs ((coordinateMSB s b).1 - (coordinateMSB s a).1) +
      Int.natAbs ((coordinateMSB s b).2 - (coordinateMSB s a).2) = 1 := by
  induction h generalizing s with
  | tail d h ih =>
      simp only [coordinateMSB]
      have hlen := h.length_eq
      rw [hlen]
      have ht := ih (next s d)
      push_cast
      simpa only [add_sub_add_left_eq_sub] using ht
  | d01 n =>
      simp only [coordinateMSB, zeroWord_length, threeWord_length]
      rw [(coordinateMSB_endpoints (next s .d1) n).1,
        (coordinateMSB_endpoints (next s .d0) n).2]
      rcases s with ⟨sw, bx, cy⟩
      cases sw <;> cases bx <;> cases cy <;>
        simp [Orient.actNat, emit, next, child, refinement, Orient.act,
          Orient.compose, Orient.choose, Nat.pow_succ] <;>
        all_goals
          have hp : 1 ≤ 2 ^ n := one_le_pow₀ (by decide)
          norm_num [Bit.toNat, Nat.cast_sub hp, Int.natAbs] <;> decide
  | d12 n =>
      simp only [coordinateMSB, zeroWord_length, threeWord_length]
      rw [(coordinateMSB_endpoints (next s .d2) n).1,
        (coordinateMSB_endpoints (next s .d1) n).2]
      rcases s with ⟨sw, bx, cy⟩
      cases sw <;> cases bx <;> cases cy <;>
        simp [Orient.actNat, emit, next, child, refinement, Orient.act,
          Orient.compose, Orient.choose, Nat.pow_succ] <;>
        all_goals
          have hp : 1 ≤ 2 ^ n := one_le_pow₀ (by decide)
          norm_num [Bit.toNat, Nat.cast_sub hp, Int.natAbs] <;> decide
  | d23 n =>
      simp only [coordinateMSB, zeroWord_length, threeWord_length]
      rw [(coordinateMSB_endpoints (next s .d3) n).1,
        (coordinateMSB_endpoints (next s .d2) n).2]
      rcases s with ⟨sw, bx, cy⟩
      cases sw <;> cases bx <;> cases cy <;>
        simp [Orient.actNat, emit, next, child, refinement, Orient.act,
          Orient.compose, Orient.choose, Nat.pow_succ] <;>
        all_goals
          have hp : 1 ≤ 2 ^ n := one_le_pow₀ (by decide)
          norm_num [Bit.toNat, Nat.cast_sub hp, Int.natAbs] <;> decide

theorem fixedPoint_succ {k n : ℕ} (hn : n + 1 < 4 ^ k) :
    planarDist (fixedPoint k n) (fixedPoint k (n + 1)) = 1 := by
  have hn0 : n < 4 ^ k := by omega
  have hlen : (fixedWord k n).reverse.length = (fixedWord k (n + 1)).reverse.length := by
    simp [fixedWord_length hn0, fixedWord_length hn]
  have hsucc : WordSucc (fixedWord k n).reverse (fixedWord k (n + 1)).reverse := by
    apply WordSucc.of_index hlen
    simp [fixedWord_index hn0, fixedWord_index hn]
  simpa [fixedPoint, planarDist] using coordinateMSB_wordSucc hsucc I

theorem fixedPoint_add_dist_le {k n r : ℕ} (hbound : n + r < 4 ^ k) :
    planarDist (fixedPoint k n) (fixedPoint k (n + r)) ≤ r := by
  induction r with
  | zero => simp [planarDist]
  | succ r ih =>
      have hprev : n + r < 4 ^ k := by omega
      have hstep : n + r + 1 < 4 ^ k := by omega
      calc
        planarDist (fixedPoint k n) (fixedPoint k (n + (r + 1))) ≤
            planarDist (fixedPoint k n) (fixedPoint k (n + r)) +
              planarDist (fixedPoint k (n + r)) (fixedPoint k (n + r + 1)) := by
                apply planarDist_triangle
        _ ≤ r + 1 := by
          rw [fixedPoint_succ hstep]
          omega

/-- The low-to-high evaluator is the same Hilbert coordinate map read backwards
from the terminal orientation. -/
theorem coordinateMSB_eq_coordinateLSB_reverse (s : Orient) (ds : List Digit) :
    coordinateMSB s ds = coordinateLSB (run s ds).2 ds.reverse := by
  induction ds generalizing s with
  | nil => rfl
  | cons d ds ih =>
      rw [show (run s (d :: ds)).2 = (run (next s d) ds).2 by rfl,
        List.reverse_cons, coordinateLSB_append]
      rw [backwardState_run_reverse]
      rw [← ih (next s d)]
      simp only [coordinateLSB, List.length_reverse, List.length_cons, List.length_nil,
        Nat.zero_add]
      rw [← backward_emit s d]
      apply Prod.ext <;> simp [coordinateMSB] <;> ring

theorem run_state_append (s : Orient) (a b : List Digit) :
    (run s (a ++ b)).2 = (run (run s a).2 b).2 := by
  induction a generalizing s with
  | nil => rfl
  | cons d ds ih => simpa [run] using ih (next s d)

theorem run_backwardState_reverse (out : Orient) (ds : List Digit) :
    (run (backwardState out ds) ds.reverse).2 = out := by
  induction ds generalizing out with
  | nil => rfl
  | cons d ds ih =>
      simp only [backwardState, List.reverse_cons, run_state_append]
      rw [ih]
      exact previous_refinement out d

theorem coordinateMSB_reverse_of_backward (a : List Digit)
    (hback : backwardState I a = I) :
    coordinateMSB I a.reverse = coordinateLSB I a := by
  have hout := run_backwardState_reverse I a
  rw [hback] at hout
  have h := coordinateMSB_eq_coordinateLSB_reverse I a.reverse
  rw [List.reverse_reverse, hout] at h
  exact h

def paddedSelected (a k : ℕ) : List Digit :=
  selectedWord a ++ zeroPairs k

@[simp] theorem paddedSelected_length (a k : ℕ) :
    (paddedSelected a k).length = (selectedWord a).length + 2 * k := by
  simp [paddedSelected]

@[simp] theorem paddedSelected_index (a k : ℕ) :
    indexLSB (paddedSelected a k) = selectedIndex selectedState a := by
  simp [paddedSelected, indexLSB_append_zeroPairs, selectedWord_index]

@[simp] theorem paddedSelected_backward (a k : ℕ) :
    backwardState I (paddedSelected a k) = I := by
  simp [paddedSelected, backwardState_append, selectedWord_backward]

@[simp] theorem paddedSelected_coordinate (a k : ℕ) :
    coordinateLSB I (paddedSelected a k) = selectedPlanar a := by
  simp [paddedSelected, coordinateLSB_append_zeroPairs, selectedWord_backward,
    selectedPlanar]

theorem paddedSelected_index_bound (a k : ℕ) :
    selectedIndex selectedState a < 4 ^ (paddedSelected a k).length := by
  have h := indexMSB_lt_pow (paddedSelected a k).reverse
  rw [indexMSB_reverse, List.length_reverse] at h
  simpa using h

theorem paddedSelected_fixedPoint (a k : ℕ) :
    fixedPoint (paddedSelected a k).length (selectedIndex selectedState a) =
      selectedPlanar a := by
  have hbound := paddedSelected_index_bound a k
  have heq : paddedSelected a k =
      fixedWord (paddedSelected a k).length (selectedIndex selectedState a) := by
    apply indexLSB_injective_of_length
    · rw [fixedWord_length hbound]
    · rw [paddedSelected_index, fixedWord_index hbound]
  rw [fixedPoint, ← heq, coordinateMSB_reverse_of_backward]
  · exact paddedSelected_coordinate a k
  · exact paddedSelected_backward a k

theorem selectedPair_fixedPoint (a b : ℕ) :
    ∃ K,
      fixedPoint K (selectedIndex selectedState a) = selectedPlanar a ∧
      fixedPoint K (selectedIndex selectedState b) = selectedPlanar b ∧
      selectedIndex selectedState b < 4 ^ K := by
  obtain ⟨ka, hka⟩ := selectedWord_length_even a
  obtain ⟨kb, hkb⟩ := selectedWord_length_even b
  let K := (selectedWord a).length + (selectedWord b).length
  have hlenA : (paddedSelected a kb).length = K := by
    rw [paddedSelected_length]
    unfold K
    omega
  have hlenB : (paddedSelected b ka).length = K := by
    rw [paddedSelected_length]
    unfold K
    omega
  refine ⟨K, ?_, ?_, ?_⟩
  · rw [← hlenA]
    exact paddedSelected_fixedPoint a kb
  · rw [← hlenB]
    exact paddedSelected_fixedPoint b ka
  · rw [← hlenB]
    exact paddedSelected_index_bound b ka

theorem selectedPlanar_succ_dist_le (a : ℕ) :
    planarDist (selectedPlanar a) (selectedPlanar (a + 1)) ≤ 28 := by
  obtain ⟨gap, _, hgap, heq⟩ := selectedIndex_succ_gap selectedState a
  obtain ⟨K, hcoordA, hcoordB, hbound⟩ := selectedPair_fixedPoint a (a + 1)
  rw [← hcoordA, ← hcoordB]
  have hd := fixedPoint_add_dist_le
    (k := K) (n := selectedIndex selectedState a) (r := gap) (by rwa [← heq])
  rw [← heq] at hd
  omega

def displacement (p q : Point3) : Point3 where
  x := q.x - p.x
  y := q.y - p.y
  z := q.z - p.z
def finiteStepMenu : Set Point3 :=
  (fun p : (ℤ × ℤ) × ℤ => { x := p.1.1, y := p.1.2, z := p.2 }) ''
    (((Set.Icc (-28 : ℤ) 28).prod (Set.Icc (-28 : ℤ) 28)).prod
      (Set.Icc (4 : ℤ) 28))

theorem finiteStepMenu_finite : finiteStepMenu.Finite := by
  apply Set.Finite.image
  exact ((Set.finite_Icc (-28 : ℤ) 28).prod (Set.finite_Icc (-28 : ℤ) 28)).prod
    (Set.finite_Icc (4 : ℤ) 28)

private theorem int_bounds_of_natAbs_le {z : ℤ} (h : z.natAbs ≤ 28) :
    -28 ≤ z ∧ z ≤ 28 := by
  cases z <;> simp [Int.natAbs] at h ⊢ <;> omega

theorem selectedLift_step_mem (a : ℕ) :
    displacement (selectedLift a) (selectedLift (a + 1)) ∈ finiteStepMenu := by
  classical
  have hplanar := selectedPlanar_succ_dist_le a
  have hxabs : Int.natAbs (((selectedPlanar (a + 1)).1 : ℤ) -
      (selectedPlanar a).1) ≤ 28 := by
    unfold planarDist at hplanar
    omega
  have hyabs : Int.natAbs (((selectedPlanar (a + 1)).2 : ℤ) -
      (selectedPlanar a).2) ≤ 28 := by
    unfold planarDist at hplanar
    omega
  have hx := int_bounds_of_natAbs_le hxabs
  have hy := int_bounds_of_natAbs_le hyabs
  have haBounds := steeringValue_bounds (selectedState a)
  have hbBounds := steeringValue_bounds (selectedState (a + 1))
  have hz : (4 : ℤ) ≤
      (selectedIndex selectedState (a + 1) : ℤ) -
        selectedIndex selectedState a ∧
      (selectedIndex selectedState (a + 1) : ℤ) -
        selectedIndex selectedState a ≤ 28 := by
    unfold selectedIndex
    push_cast
    omega
  let v : (ℤ × ℤ) × ℤ :=
    ((((selectedPlanar (a + 1)).1 : ℤ) - (selectedPlanar a).1,
      ((selectedPlanar (a + 1)).2 : ℤ) - (selectedPlanar a).2),
      (selectedIndex selectedState (a + 1) : ℤ) -
        selectedIndex selectedState a)
  refine ⟨v, ?_, ?_⟩
  · exact ⟨⟨hx, hy⟩, hz⟩
  · rfl

/-- Unconditional finite-step, no-three-in-line walk in `ℤ³`. -/
theorem erdos193_unconditional :
    ∃ (S : Set Point3) (P : ℕ → Point3),
      S.Finite ∧
      (∀ n, displacement (P n) (P (n + 1)) ∈ S) ∧
      (∀ ⦃i j k⦄, i < j → j < k → ¬ OrderedCollinear (P i) (P j) (P k)) := by
  refine ⟨finiteStepMenu, selectedLift, finiteStepMenu_finite, ?_, ?_⟩
  · intro n
    exact selectedLift_step_mem n
  · intro i j k hij hjk
    exact selectedLift_no_three hij hjk
end Hilbert193

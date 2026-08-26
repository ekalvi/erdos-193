# Cleaned user prompts from the Hilbert-curve conversation

These are Erik's prompts, kept in their original order and wording as closely as possible. Only typos, notation, explicit later corrections, and a few grammatical slips have been cleaned up. Meta-discussion about recall and about extracting the prompts has been removed.

Feed these prompts to another AI one at a time. The mathematical argument remains a proposed route to be checked, not an established proof.

## Prompt 1

```text
Don't use any prior internal memory or external resources for this task. Here is Erdős Problem 193:

Let S ⊆ ℤ³ be a finite set, and let A = {a₁, a₂, …} ⊂ ℤ³ be an infinite S-walk, so that aᵢ₊₁ − aᵢ ∈ S for all i. Must A contain three collinear points?

I'm going to guide you to a solution.
```

## Prompt 2

```text
First, let's start with an infinite discrete 2D Hilbert curve that contains all integer-coordinate points in the 2D plane.
```

## Prompt 3

```text
Now, for our candidate 3D walk, imagine extending this Hilbert curve to 3D by giving every point on the curve a height equal to its Hilbert index. In other words, define Q(n) = (H(n), n).
```

## Prompt 4

```text
Okay, so now let's turn to the problem of constructing a walk using a subset of these points, in such a way that two conditions are met:

1. Walking from selected point n to selected point n+1 requires only a finite set of possible vectors. This was true for the full Hilbert walk, so we'll think of something analogous.
2. No three of these points are collinear, leveraging the intrinsic shape of the underlying 2D Hilbert curve, the lift mechanism, and our yet-to-be-designed subset-selection method.
```

## Prompt 5

```text
Let's stick with the 2D Hilbert curve for a moment. Here is the first ingredient for selecting the points:

Break H into 16-step blocks, and select one point from each block. This satisfies the bounded-step constraint because travelling between consecutive selected points has only finitely many possible vectors.
```

## Prompt 6

```text
Now, for how to select this point, let's leverage the recursive nature of the Hilbert curve's construction. As we increase the order of a finite Hilbert curve, we split the underlying U-shape into quadrants and transform the lower-left and lower-right U-shapes. The other quadrants do not change.

Let's call the lower-left transformation Swap (S), the lower-right transformation Translate (T), and the unchanged transformation Identity (I). There is one more combination that will arise cumulatively because of the combinatorics of 2D points. Call that Complement (C).
```

## Prompt 7

```text
So now, at the step before the recursion, every point carries one of these four states—S, I, T, or C—so that the state can be applied to the next U-shape once we split it into quadrants again.
```

## Prompt 8

```text
Okay, for our construction, we're going to pick only points whose terminal state, defined as above, is I.
```

## Prompt 9

```text
To guarantee a single selection per 16-step block, let's agree on a convention. It will be a map that selects an integer offset from the first point of the block, based on that first point's terminal state.

If the state is S, we always use the same offset; if it is I, we use another fixed offset; and so on. Pick each integer so that we end on an I point, select only that point for the block, and then move on.
```

## Prompt 10

```text
Instead of the offsets 0, 1, 7, 3, let's choose 5, 1, 13, 3 for the states S, I, T, C, respectively.
```

## Prompt 11

```text
So now we have an infinite walk with a finite menu of step vectors, in which all selected points have terminal state I.
```

## Prompt 12

```text
Let's tackle this by developing a theorem that is true for any two points in this "same-state" Hilbert walk in 2D, and then use it to our advantage when tackling collinearity or non-collinearity in 3D.

In 2D, examine any two points in our selection, H(m) and H(n), where m and n are the integer indices of the points we are choosing. Write H(n) = (xₙ, yₙ).

Our theorem is going to relate the index offset m − n to the planar vector displacement H(m) − H(n). Remember, the index offset is also the height difference in 3D. For consecutive selected points, the planar displacement and index offset lift to a vector from a single finite menu:

(H(m) − H(n), m − n).
```

## Prompt 13

```text
Okay, for the Hilbert pair theorem that we're going to need later:

1. Take ν₂(m − n), where ν₂ is the 2-adic valuation of the index offset.
2. Let's develop a function called the "vector fingerprint" that extends the 2-adic concept to 2D. For a planar displacement (Δx, Δy), define

V(Δx, Δy) = 2 min{ν₂(Δx), ν₂(Δy)}.

There is also a separate parity term: add 1 when ν₂(Δx) = ν₂(Δy), and add 0 when they are not equal.

These are the two ingredients we'll need as part of the Hilbert pair theorem.
```

## Prompt 14

```text
Okay, we know what we want to establish for selected same-terminal-state points with indices m and n:

ν₂(m − n)
=
V(H(m) − H(n))
+
1_{ν₂(Δx) = ν₂(Δy)},

where (Δx, Δy) = H(m) − H(n).

We're going to do that by looking at the values of m and n in base 4 and comparing their common suffix digits. We'll do something similar for the x- and y-coordinates, but written in binary. Let's start with ν₂(m − n) first.
```

## Prompt 15

```text
Okay, now we're going to do the same with H(m) − H(n). This will require the terminal states to agree for the relation to hold.

Figure out how a Hilbert index n in base 4 decodes to H(n) = (xₙ, yₙ) in binary, keeping in mind how the recursion transforms the digits as we move to higher precision. Once you do that, demonstrate how the base-4 index (1332)₄ maps to its x- and y-coordinates in binary.
```

## Prompt 16

```text
Let's take another stab at this in a different way.

What we should do is read the Hilbert index in base 4 from left to right and use the Gray code to determine the binary x- and y-bits for each digit. You have to transform each digit according to its Hilbert state, however.
```

## Prompt 17

```text
Now, looking at V(H(n) − H(m)), it follows that if m and n have a matching suffix of j digits in base 4, then the binary x- and y-coordinates of H(n) and H(m) will have matching suffixes of j bits. Thus, each coordinate of the planar difference H(n) − H(m) will be divisible by 2ʲ.
```

## Prompt 18

```text
However, you need to remember to look at the difference in x and y after factoring out the common powers of 2.

Because of the Gray code, both bits will be different if the first differing base-4 digits of m and n differ by 2, while only one bit will be different if those digits have opposite parity. When applying the parity portion of the Hilbert pair law, you get +1 in the first case because ν₂(Δx) = ν₂(Δy).
```

## Prompt 19

```text
Doesn't that prove the Hilbert pair law?
```

## Prompt 20

```text
Now, given this setup, we have enough to prove a negative answer to Erdős Problem 193:

- Assume that points Q(a), Q(b), and Q(c) in our construction are collinear.
- Let the index offset from a to b be A, and the offset from b to c be B. Let the corresponding planar vectors be

  X = H(b) − H(a)

  and

  Y = H(c) − H(b).

- Since the lifted points are collinear,

  X/A = Y/B.

- Remove gcd(A, B). Call it g, so that

  A = gr

  and

  B = gs,

  where gcd(r, s) = 1. Therefore, r and s cannot both be even.

- Apply the Hilbert pair law to the adjacent pairs (a, b) and (b, c). You'll discover that r and s must be odd.
- Apply the pair law to the endpoint pair (a, c), and you'll find that r + s is odd.
- But two odd numbers must add to an even number.
- Contradiction. QED.
```

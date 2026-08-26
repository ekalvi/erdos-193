# Minimal Prompt Outline for the Hilbert-Walk Proof

- Define an infinite discrete downward-U Hilbert walk \(H:\mathbb N\to\mathbb Z^2\), and lift it by
  \[
  Q(n)=(H(n),n).
  \]

- Partition the indices into blocks \(\{16k,\ldots,16k+15\}\). Label Hilbert points by terminal states \(S,I,T,C\), where \(S\) swaps coordinates, \(T\) is the lower-right transformation, and \(C=ST\).

- From each block select one terminal-\(I\) point using offsets
  \[
  o(S)=5,\qquad o(I)=1,\qquad o(T)=13,\qquad o(C)=3.
  \]
  The selected-index gaps are bounded, so the lifted sequence uses only finitely many step vectors.

- Decode Hilbert indices from left to right in base \(4\), using the downward-U Gray code
  \[
  0\mapsto00,\qquad 1\mapsto01,\qquad 2\mapsto11,\qquad 3\mapsto10,
  \]
  transformed according to the current Hilbert state.

- Prove the Hilbert pair law for same-terminal-state indices \(m,n\):
  \[
  \nu_2(m-n)
  =
  2\min\{\nu_2(\Delta x),\nu_2(\Delta y)\}
  +\mathbf 1_{\nu_2(\Delta x)=\nu_2(\Delta y)},
  \]
  where \((\Delta x,\Delta y)=H(m)-H(n)\). Use their common base-\(4\) suffix and the corresponding common binary coordinate suffix.

- Assume \(Q(a),Q(b),Q(c)\) are collinear. Write
  \[
  b-a=gr,\qquad c-b=gs,\qquad \gcd(r,s)=1.
  \]
  Collinearity gives planar differences \(X=rZ\) and \(Y=sZ\).

- Apply the pair law to \((a,b)\) and \((b,c)\) to prove that \(r,s\) are both odd. Apply it to \((a,c)\) to prove that \(r+s\) is odd, contradicting that the sum of two odd integers is even. Therefore the constructed finite-step walk has no three collinear points.

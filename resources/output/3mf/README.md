# Implicit 3MF examples

These files use the 3MF Volumetric and Implicit extensions. Open them with an
extension-aware application such as Gladius. A conventional 3MF mesh viewer may
reject the required extensions or show only the evaluation domain.

All coordinates and distances are in millimetres.

## Common structure

Each file is an OPC ZIP package containing:

- `[Content_Types].xml`, which declares the package content types;
- `_rels/.rels`, which points to the 3D model part; and
- `3D/3dmodel.model`, which contains the implicit function and model objects.

The model part has three resources:

1. Implicit function `1` accepts the position vector `pos` and returns the
   scalar channel `shape`.
2. Mesh object `2` is a closed box defining the function's evaluation bounds.
3. Object `3` contains a volumetric `levelset` that connects function `1` to
   mesh `2`. The build item selects this object.

The level-set surface is where the returned value is zero. Values below zero
are inside the shape and values above zero are outside it.

For a point

$$
\mathbf{p} = (x, y, z),
$$

the examples use the following Constructive Solid Geometry operations:

$$
\begin{aligned}
d_{A \cup B}(\mathbf{p}) &= \min(d_A(\mathbf{p}), d_B(\mathbf{p})), \\
d_{A \cap B}(\mathbf{p}) &= \max(d_A(\mathbf{p}), d_B(\mathbf{p})), \\
d_{A \setminus B}(\mathbf{p}) &= \max(d_A(\mathbf{p}), -d_B(\mathbf{p})).
\end{aligned}
$$

These are hard Boolean operations. No smoothing is applied.

## 1. Sphere

File: `01_sphere.3mf`

The sphere is centred at the origin and has radius $r = 20$:

$$
d_{sphere}(\mathbf{p}) = \lVert \mathbf{p} \rVert - 20.
$$

The graph computes `length(pos)` and subtracts the radius. Its evaluation box
has half-extents $(26, 26, 26)$.

## 2. Box

File: `02_box.3mf`

The box is centred at the origin and has half-size
$\mathbf{b} = (20, 16, 13)$. First compute

$$
\mathbf{q} = |\mathbf{p}| - \mathbf{b}.
$$

The signed-distance function is

$$
d_{box}(\mathbf{p}) =
\lVert \max(\mathbf{q}, \mathbf{0}) \rVert
+ \min(\max(q_x, \max(q_y, q_z)), 0).
$$

The vector `abs`, `subtraction`, `max`, `length`, and scalar `min` nodes form
this expression. Its evaluation box has half-extents $(26, 22, 19)$.

## 3. Torus

File: `03_torus.3mf`

The torus is centred at the origin and lies around the Z axis. Its major radius
is $R = 22$ and its tube radius is $r = 7$:

$$
d_{torus}(\mathbf{p}) =
\sqrt{\left(\sqrt{x^2 + y^2} - 22\right)^2 + z^2} - 7.
$$

The graph decomposes `pos`, computes the radial XY length, subtracts the major
radius, then computes the tube distance. Its evaluation box has half-extents
$(34, 34, 14)$.

## 4. Union of two spheres

File: `04_union_two_spheres.3mf`

Both spheres have radius $18$, with centres
$\mathbf{c}_L = (-10, 0, 0)$ and $\mathbf{c}_R = (10, 0, 0)$:

$$
\begin{aligned}
d_L(\mathbf{p}) &= \lVert \mathbf{p} - \mathbf{c}_L \rVert - 18, \\
d_R(\mathbf{p}) &= \lVert \mathbf{p} - \mathbf{c}_R \rVert - 18, \\
d(\mathbf{p}) &= \min(d_L(\mathbf{p}), d_R(\mathbf{p})).
\end{aligned}
$$

Each centre is handled by a vector subtraction before the sphere calculation.
A final `min` node joins them. The evaluation box has half-extents
$(34, 25, 25)$.

## 5. Intersection of two spheres

File: `05_intersection_two_spheres.3mf`

This uses the same two spheres as the union example, but keeps only their common
volume:

$$
d(\mathbf{p}) = \max(d_L(\mathbf{p}), d_R(\mathbf{p})).
$$

The result is a lens shape. A final `max` node performs the intersection. The
evaluation box has half-extents $(25, 25, 25)$.

## 6. Sphere minus sphere

File: `06_subtract_two_spheres.3mf`

The base sphere has centre $(-5, 0, 0)$ and radius $22$. The cutter has centre
$(10, 0, 0)$ and radius $18$:

$$
\begin{aligned}
d_A(\mathbf{p}) &= \lVert \mathbf{p} - (-5,0,0) \rVert - 22, \\
d_B(\mathbf{p}) &= \lVert \mathbf{p} - (10,0,0) \rVert - 18, \\
d(\mathbf{p}) &= \max(d_A(\mathbf{p}), -d_B(\mathbf{p})).
\end{aligned}
$$

The graph negates the cutter distance with multiplication by $-1$, then applies
`max`. The evaluation box has half-extents $(33, 29, 29)$.

## 7. Union of a box and sphere

File: `07_union_box_sphere.3mf`

The box has centre $(-7, 0, 0)$ and half-size $(16, 14, 13)$. The sphere has
centre $(12, 0, 0)$ and radius $17$. Let their distance functions be $d_B$ and
$d_S$:

$$
d(\mathbf{p}) = \min(d_B(\mathbf{p}), d_S(\mathbf{p})).
$$

The box and sphere graphs are built independently and connected to a final
`min` node. The evaluation box has half-extents $(35, 25, 24)$.

## 8. Intersection of a box and sphere

File: `08_intersection_box_sphere.3mf`

This uses the same box and sphere as the previous example, but returns only
their common volume:

$$
d(\mathbf{p}) = \max(d_B(\mathbf{p}), d_S(\mathbf{p})).
$$

A final `max` node performs the intersection. The evaluation box has
half-extents $(28, 23, 22)$.

## 9. Box minus sphere

File: `09_subtract_sphere_from_box.3mf`

The box is centred at the origin with half-size $(20, 16, 14)$. The spherical
cutter has centre $(13, 0, 0)$ and radius $18$:

$$
\begin{aligned}
d_B(\mathbf{p}) &= d_{box}(\mathbf{p}; (20,16,14)), \\
d_S(\mathbf{p}) &= \lVert \mathbf{p} - (13,0,0) \rVert - 18, \\
d(\mathbf{p}) &= \max(d_B(\mathbf{p}), -d_S(\mathbf{p})).
\end{aligned}
$$

The negated sphere removes an offset curved section from the box. The evaluation
box has half-extents $(27, 23, 21)$.


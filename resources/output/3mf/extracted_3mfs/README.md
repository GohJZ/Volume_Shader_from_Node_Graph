# Implicit 3MF examples

These files use the published 3MF Volumetric and Implicit extensions. Open them
with an extension-aware application such as Gladius. A conventional 3MF mesh
viewer may reject the required extensions or show only the evaluation domain.

All dimensions are in millimetres. Each package contains one implicit function,
one closed bounding mesh, and one level-set object selected by the build item.

| File | Expected shape |
| --- | --- |
| `01_sphere.3mf` | Sphere with radius 20 |
| `02_box.3mf` | Box with half-size `(20, 16, 13)` |
| `03_torus.3mf` | Torus with major radius 22 and tube radius 7 |
| `04_union_two_spheres.3mf` | Two overlapping spheres joined with `min` |
| `05_intersection_two_spheres.3mf` | Lens-shaped overlap of two spheres |
| `06_subtract_two_spheres.3mf` | A sphere with an offset spherical cut |
| `07_union_box_sphere.3mf` | Hard union of an offset box and sphere |
| `08_intersection_box_sphere.3mf` | Common volume of a box and sphere |
| `09_subtract_sphere_from_box.3mf` | A box with an offset spherical cut |

Regenerate and validate all examples with:

```bash
python generate_3mf_examples.py
```

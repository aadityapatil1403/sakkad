# Demo Dataset Evaluation

## Evaluation Table

| image | expected taxonomy | actual top match | pass/fail |
| --- | --- | --- | --- |
| western.jpg | Deconstructed Classics | Cowboy Core | FAIL |
| vintage.jpg | New Americana | 70s Revival | FAIL |
| workwear.jpg | Deconstructed Classics | Workwear | PASS |
| leather_jacket.jpg | Archive Fashion | Biker | PASS |
| japanjersey.jpg | Color Blocking | Sportswear Luxe | PASS |
| soccer_streetwear.jpg | Draped Form | Streetwear | PASS |
| monochromatic.jpg | Neo-Romantic | Biker | FAIL |
| formal_wear.jpg | Deconstructed Classics | Soft Tailoring | PASS |
| furcoat.jpg | Archive Fashion | Y2K | PASS |
| old_money.jpg | Color Blocking | Preppy | PASS |
| western.jpg | Deconstructed Classics | Cowboy Core | FAIL |
| monochromatic.jpg | Neo-Romantic | Biker | FAIL |
| formal_wear.jpg | Deconstructed Classics | Soft Tailoring | PASS |
| leather_jacket.jpg | Archive Fashion | Biker | PASS |
| workwear.jpg | Deconstructed Classics | Workwear | PASS |
| vintage.jpg | New Americana | 70s Revival | FAIL |
| japanjersey.jpg | Color Blocking | Sportswear Luxe | PASS |
| soccer_streetwear.jpg | Draped Form | Streetwear | PASS |
| old_money.jpg | Color Blocking | Preppy | PASS |
| furcoat.jpg | Archive Fashion | Y2K | PASS |
| monochromatic.jpg | Neo-Romantic | Biker | FAIL |
| formal_wear.jpg | Deconstructed Classics | Soft Tailoring | PASS |
| western.jpg | Deconstructed Classics | Cowboy Core | FAIL |
| vintage.jpg | New Americana | 70s Revival | FAIL |
| leather_jacket.jpg | Archive Fashion | Biker | PASS |

## Weak Cases

- `western.jpg`: Cowboy Core | Ranch tailoring in suede and denim (0.1175) | Taxonomy mismatch: expected one of ['Deconstructed Classics', 'Western Americana', 'Archive Fashion', 'Avant-garde'], got Cowboy Core.
- `vintage.jpg`: 70s Revival | Silent ranch essentials (0.0917) | Taxonomy mismatch: expected one of ['New Americana', 'Vintage Americana', 'Denim Culture', 'Western Americana'], got 70s Revival. Reference score low: 0.0917 <= 0.10.
- `leather_jacket.jpg`: Biker | Distressed moto denim hybrids (0.0616) | Reference score low: 0.0616 <= 0.10.
- `japanjersey.jpg`: Sportswear Luxe | Graphic rock tee obsession (0.0333) | Reference score low: 0.0333 <= 0.10.
- `soccer_streetwear.jpg`: Streetwear | Deformed sole streetwear (0.0766) | Reference score low: 0.0766 <= 0.10.
- `monochromatic.jpg`: Biker | Slim rocker moto (0.0897) | Taxonomy mismatch: expected one of ['Neo-Romantic', 'Monochrome', '90s Minimalism', 'Soft Tailoring'], got Biker. Reference score low: 0.0897 <= 0.10.
- `formal_wear.jpg`: Soft Tailoring | Soft urban uniform (0.0618) | Reference score low: 0.0618 <= 0.10.
- `furcoat.jpg`: Y2K | Distressed moto denim hybrids (0.0916) | Reference score low: 0.0916 <= 0.10.
- `old_money.jpg`: Preppy | Industrial uniform basics (0.0471) | Reference score low: 0.0471 <= 0.10.
- `western.jpg`: Cowboy Core | Ranch tailoring in suede and denim (0.1175) | Taxonomy mismatch: expected one of ['Deconstructed Classics', 'Western Americana', 'Archive Fashion', 'Avant-garde'], got Cowboy Core.
- `monochromatic.jpg`: Biker | Slim rocker moto (0.0897) | Taxonomy mismatch: expected one of ['Neo-Romantic', 'Monochrome', '90s Minimalism', 'Soft Tailoring'], got Biker. Reference score low: 0.0897 <= 0.10.
- `formal_wear.jpg`: Soft Tailoring | Soft urban uniform (0.0618) | Reference score low: 0.0618 <= 0.10.
- `leather_jacket.jpg`: Biker | Distressed moto denim hybrids (0.0616) | Reference score low: 0.0616 <= 0.10.
- `vintage.jpg`: 70s Revival | Silent ranch essentials (0.0917) | Taxonomy mismatch: expected one of ['New Americana', 'Vintage Americana', 'Denim Culture', 'Western Americana'], got 70s Revival. Reference score low: 0.0917 <= 0.10.
- `japanjersey.jpg`: Sportswear Luxe | Graphic rock tee obsession (0.0333) | Reference score low: 0.0333 <= 0.10.
- `soccer_streetwear.jpg`: Streetwear | Deformed sole streetwear (0.0766) | Reference score low: 0.0766 <= 0.10.
- `old_money.jpg`: Preppy | Industrial uniform basics (0.0471) | Reference score low: 0.0471 <= 0.10.
- `furcoat.jpg`: Y2K | Distressed moto denim hybrids (0.0916) | Reference score low: 0.0916 <= 0.10.
- `monochromatic.jpg`: Biker | Slim rocker moto (0.0897) | Taxonomy mismatch: expected one of ['Neo-Romantic', 'Monochrome', '90s Minimalism', 'Soft Tailoring'], got Biker. Reference score low: 0.0897 <= 0.10.
- `formal_wear.jpg`: Soft Tailoring | Soft urban uniform (0.0618) | Reference score low: 0.0618 <= 0.10.
- `western.jpg`: Cowboy Core | Ranch tailoring in suede and denim (0.1175) | Taxonomy mismatch: expected one of ['Deconstructed Classics', 'Western Americana', 'Archive Fashion', 'Avant-garde'], got Cowboy Core.
- `vintage.jpg`: 70s Revival | Silent ranch essentials (0.0917) | Taxonomy mismatch: expected one of ['New Americana', 'Vintage Americana', 'Denim Culture', 'Western Americana'], got 70s Revival. Reference score low: 0.0917 <= 0.10.
- `leather_jacket.jpg`: Biker | Distressed moto denim hybrids (0.0616) | Reference score low: 0.0616 <= 0.10.

## Missing / Manual Assets

- None.

## Safest Live Demo Images

- `workwear.jpg`
- `workwear.jpg`
- `western.jpg`

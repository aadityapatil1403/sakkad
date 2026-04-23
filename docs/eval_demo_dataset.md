# Demo Dataset Evaluation

## Evaluation Table

| image | expected taxonomy | actual top match | pass/fail |
| --- | --- | --- | --- |
| leaf.jpg | Botanical Organic | Botanical Organic | PASS |
| tree_bark.jpg | Botanical Organic | Botanical Organic | PASS |
| closeup_flower.jpg | Botanical Organic | Botanical Organic | PASS |
| concrete_wall.jpg | Concrete Brutalism | Concrete Brutalism | PASS |
| red-brick-wall.jpg | Layered Grain | Layered Grain | PASS |
| rusted_pipes.jpg | Oxidized Metal | Oxidized Metal | PASS |
| neon_sign.jpg | Neon Lit Night | Neon Lit Night | PASS |
| leather_bag.jpg | Patinated Finish | Patinated Finish | PASS |
| cofee_cup.jpg | Cellular Pattern | Cellular Pattern | PASS |
| western.jpg | Cowboy Core | Cowboy Core | PASS |
| workwear.jpg | Workwear | Workwear | PASS |
| leather_jacket.jpg | Biker | Biker | PASS |
| vintage.jpg | 70s Revival | 70s Revival | PASS |
| formal_wear.jpg | Soft Tailoring | Soft Tailoring | PASS |
| furcoat.jpg | Y2K | Y2K | PASS |
| soccer_streetwear.jpg | Streetwear | Streetwear | PASS |
| old_money.jpg | Preppy | Preppy | PASS |
| monochromatic.jpg | Monochrome | Biker | FAIL |
| ripped_jean.jpg | Denim-on-Denim | Denim-on-Denim | PASS |

## Weak Cases

- `leaf.jpg`: Botanical Organic | Light through pleated leaf geometry (-0.0211) | Reference score low: -0.0211 <= 0.10.
- `tree_bark.jpg`: Botanical Organic | Organic mass as structural rupture (-0.0137) | Reference score low: -0.0137 <= 0.10.
- `closeup_flower.jpg`: Botanical Organic | Technical cargo architecture (-0.0249) | Reference score low: -0.0249 <= 0.10.
- `concrete_wall.jpg`: Concrete Brutalism | Architectural silence in matte concrete tone (0.0836) | Reference score low: 0.0836 <= 0.10.
- `red-brick-wall.jpg`: Layered Grain | Original perfecto hardware (-0.0045) | Reference score low: -0.0045 <= 0.10.
- `rusted_pipes.jpg`: Oxidized Metal | Oxidized surface and patinated finish (0.0601) | Reference score low: 0.0601 <= 0.10.
- `neon_sign.jpg`: Neon Lit Night | Weathered signage and institutional surface (0.0269) | Reference score low: 0.0269 <= 0.10.
- `leather_bag.jpg`: Patinated Finish | Waxed road captain fieldwear (0.0125) | Reference score low: 0.0125 <= 0.10.
- `cofee_cup.jpg`: Cellular Pattern | Technical cargo architecture (-0.0122) | Reference score low: -0.0122 <= 0.10.
- `leather_jacket.jpg`: Biker | Distressed moto denim hybrids (0.0616) | Reference score low: 0.0616 <= 0.10.
- `vintage.jpg`: 70s Revival | Silent ranch essentials (0.0917) | Reference score low: 0.0917 <= 0.10.
- `formal_wear.jpg`: Soft Tailoring | Soft urban uniform (0.0618) | Reference score low: 0.0618 <= 0.10.
- `furcoat.jpg`: Y2K | Distressed moto denim hybrids (0.0916) | Reference score low: 0.0916 <= 0.10.
- `soccer_streetwear.jpg`: Streetwear | Deformed sole streetwear (0.0766) | Reference score low: 0.0766 <= 0.10.
- `old_money.jpg`: Preppy | Industrial uniform basics (0.0471) | Reference score low: 0.0471 <= 0.10.
- `monochromatic.jpg`: Biker | Slim rocker moto (0.0897) | Taxonomy mismatch: expected one of ['Monochrome'], got Biker. Reference score low: 0.0897 <= 0.10.
- `ripped_jean.jpg`: Denim-on-Denim | Distressed moto denim hybrids (0.0566) | Reference score low: 0.0566 <= 0.10.

## Missing / Manual Assets

- None.

## Safest Live Demo Images

- `workwear.jpg`
- `western.jpg`

# Demo Dataset Evaluation

## Scope

This document tracks the demo corpus used for the Spectacles -> web app walkthrough. The source of truth for target captures is `sakad-backend/eval/demo_dataset_manifest.json`.

- Total target captures: 34
- Available local images right now: 10
- Remaining assets: 24 manual-add placeholders
- Demo session aliases: `session_fashion`, `session_abstract`, `session_mixed`
- Latest script attempt: `2026-04-21`
- Latest runtime blocker: `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are not set in the current shell, so the live seed/eval run has not completed yet

## Evaluation Table

Run `python scripts/seed_demo_captures.py` from `sakad-backend/` to refresh actual results. Until then, use the table below as the expected-vs-run checklist.

| image | expected taxonomy | actual top match | pass/fail |
| --- | --- | --- | --- |
| western.jpg | Western Americana, Cowboy Core | Pending script run | Pending |
| vintage.jpg | Vintage Americana, 70s Revival | Pending script run | Pending |
| western_rodeo_denim_01.jpg | Western Americana | Missing local asset | Fail |
| western_bootcut_suede_01.jpg | Cowboy Core | Missing local asset | Fail |
| americana_fringe_hat_01.jpg | New Americana | Missing local asset | Fail |
| workwear.jpg | Workwear, Utilitarian | Pending script run | Pending |
| leather_jacket.jpg | Biker, Moto Culture | Pending script run | Pending |
| utility_vest_olive_01.jpg | Utilitarian | Missing local asset | Fail |
| carpenter_pants_canvas_01.jpg | Workwear | Missing local asset | Fail |
| field_jacket_functional_01.jpg | Quiet Outdoors | Missing local asset | Fail |
| japanjersey.jpg | Japanese Streetwear, Streetwear | Pending script run | Pending |
| soccer_streetwear.jpg | Streetwear, Sportswear Luxe | Pending script run | Pending |
| tokyo_track_jacket_01.jpg | Japanese Streetwear | Missing local asset | Fail |
| sporty_layered_jersey_01.jpg | Sportswear Luxe | Missing local asset | Fail |
| harajuku_oversized_01.jpg | Maximalism | Missing local asset | Fail |
| monochromatic.jpg | Monochrome, 90s Minimalism | Pending script run | Pending |
| formal_wear.jpg | Tailoring, Soft Tailoring | Pending script run | Pending |
| minimal_black_coat_01.jpg | Techno Minimalism | Missing local asset | Fail |
| white_gallery_minimal_01.jpg | 90s Minimalism | Missing local asset | Fail |
| oversized_neutral_suit_01.jpg | Oversized Structure | Missing local asset | Fail |
| architectural_shadow_01.jpg | Avant-garde | Missing local asset | Fail |
| brutalist_stairwell_01.jpg | Techno Minimalism | Missing local asset | Fail |
| greenhouse_texture_01.jpg | Artisan Craft | Missing local asset | Fail |
| rust_texture_macro_01.jpg | Artisan Craft | Missing local asset | Fail |
| stone_wall_pattern_01.jpg | Deconstructed Classics | Missing local asset | Fail |
| desert_plant_silhouette_01.jpg | Quiet Outdoors | Missing local asset | Fail |
| window_reflection_grid_01.jpg | Color Blocking | Missing local asset | Fail |
| concrete_curve_01.jpg | Draped Form | Missing local asset | Fail |
| furcoat.jpg | Y2K, Club Kid | Pending script run | Pending |
| old_money.jpg | Old Money, Preppy | Pending script run | Pending |
| editorial_red_background_01.jpg | Color Blocking | Missing local asset | Fail |
| archive_runway_pose_01.jpg | Archive Fashion | Missing local asset | Fail |
| romantic_sheer_editorial_01.jpg | Neo-Romantic | Missing local asset | Fail |
| deconstructed_layered_editorial_01.jpg | Deconstructed Classics | Missing local asset | Fail |

## Weak Cases

- `western.jpg`: already called out in `CONTINUITY.md` as a likely taxonomy-quality weak case; validate whether top taxonomy still lands outside western labels.
- `furcoat.jpg`: also called out as a likely weak taxonomy case; review whether retrieval is stronger than taxonomy here.
- Any capture whose top reference score is `<= 0.10` should be treated as weak even if the taxonomy top match is plausible.
- Abstract or environmental placeholders are the highest risk group because the taxonomy is fashion-first and may collapse them into irrelevant apparel labels.

## Missing / Manual Assets

These placeholders should be filled with royalty-free images from Unsplash or Pexels before the live demo:

- Western / Americana: `western_rodeo_denim_01.jpg`, `western_bootcut_suede_01.jpg`, `americana_fringe_hat_01.jpg`
- Workwear / Utility: `utility_vest_olive_01.jpg`, `carpenter_pants_canvas_01.jpg`, `field_jacket_functional_01.jpg`
- Japanese Streetwear / Sporty: `tokyo_track_jacket_01.jpg`, `sporty_layered_jersey_01.jpg`, `harajuku_oversized_01.jpg`
- Minimalism / Monochrome: `minimal_black_coat_01.jpg`, `white_gallery_minimal_01.jpg`, `oversized_neutral_suit_01.jpg`
- Abstract / Environmental: `architectural_shadow_01.jpg`, `brutalist_stairwell_01.jpg`, `greenhouse_texture_01.jpg`, `rust_texture_macro_01.jpg`, `stone_wall_pattern_01.jpg`, `desert_plant_silhouette_01.jpg`, `window_reflection_grid_01.jpg`, `concrete_curve_01.jpg`
- Mixed / Editorial: `editorial_red_background_01.jpg`, `archive_runway_pose_01.jpg`, `romantic_sheer_editorial_01.jpg`, `deconstructed_layered_editorial_01.jpg`

## Safest Live Demo Images

Use these first once the seeding script confirms their outputs:

- `workwear.jpg`
- `japanjersey.jpg`
- `soccer_streetwear.jpg`
- `formal_wear.jpg`
- `old_money.jpg`

## Recommendation

For the live walkthrough, anchor the narrative on the currently available fashion-forward images first and keep abstract/environmental captures as optional second-pass material until more real assets are added and reference scores are validated.

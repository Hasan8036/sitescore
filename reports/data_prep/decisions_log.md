# Data preparation decisions

- Restaurants: 52,268; closed: 17,281 (33.1%)
- Restaurants = businesses whose categories contain the exact token 'Restaurants' and that have coordinates.
- Metro = nearest of 11 metro centres by straight-line distance; checked against the state field.
- Missing price kept as its own 'Missing' category (not dropped).
- Cuisine group = first match in a fixed priority list (cuisines, then formats, then American, then Other).
- Chain = normalized name appears at >= 5 restaurants; cutoffs [3, 5, 10] saved for robustness.
- Competition counts include open and closed restaurants; no neighbour closure rates, ratings or reviews used.
- Counts log-transformed as log(1 + count) because of heavy right skew.
- Same-cuisine competition measured as a share of all nearby restaurants (0 when there are none), replacing the raw count, which correlated 0.82 with the total count.
- Price gap: missing flag added and gap filled with 0; abs_price_gap measures distance from local price in either direction.
- n_open_rest (open neighbours only) computed for a robustness check of the density finding; not a model input.
- Largest metro (Philadelphia) not recommended as the held-out metro; suggest a mid-sized metro, plus leave-one-metro-out as a robustness check.

## Recommended model inputs (main specification)

- `price_tier`
- `cuisine_group`
- `is_chain`
- `log_n_rest_500m`
- `same_cuisine_share_500m`
- `abs_price_gap`
- `price_gap_missing`
- `metro`

Robustness: other radii (250 m, 1 km), chain cutoffs 3 and 10, open-neighbour counts, leave-one-metro-out.

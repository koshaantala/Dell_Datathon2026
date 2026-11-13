# Data

## hill_country_sites.csv

50 assessed locations along the Guadalupe River (Hunt to Comfort, Kerr and Kendall
counties). Each row is one NOAA aerial image tile from after the July 2025 floods, with
its matched context from the UTSA Texas Flood Student Data (`image_metadata.csv`,
consolidated November 10, 2026).

Built by `scripts/extract_sites.py`. It keeps rows whose `image_id` starts with `HC` and
which have a precise footprint, plus only the columns the site uses. The four USCG
rescue images (`AF*`) are excluded: they have no precise location.

Rebuild after the dataset changes:

```sh
make data SOURCE_CSV=../UTSA-flood-images/image_metadata.csv
```

### Meaning of the key columns

| Column | Meaning |
| --- | --- |
| `fema_flood_zones`, `fema_zone_subtypes` | FEMA zone at the tile centre (current snapshot) |
| `elevation_m` | Ground elevation at the tile centre, NAVD 88 |
| `terrain_elevation_min_m` | Lowest ground in the tile; the score uses `elevation_m` minus this |
| `nearest_high_water_mark_distance_km` | Distance to the nearest July 2025 high-water mark (post-event evidence) |
| `usgs_gage_height_station_*` | Nearest USGS gauge and its distance |
| `source_url` | The spot in NOAA's July 2025 imagery viewer |

Imagery: NOAA National Geodetic Survey, CC0-1.0.

## replay/

`make replay` writes `replay/july2025.json` with USGS gauge heights for the Night Watch
replay. Not included until someone runs it with internet access.

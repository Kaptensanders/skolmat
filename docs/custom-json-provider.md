# Custom JSON provider

`CustomJsonMenu` (`custom_components/skolmat/menu.py`) is the catch-all provider used by
`Menu.createMenu()` whenever a configured URL does not match one of the recognized
providers (`skolmaten.se`, `foodit.se`, `menu.matildaplatform.com`, `mashie`, `mateo.se`,
`meny.skolmat.info`, `menugo.se`). It lets a school (or anyone hosting a static file) publish
a menu as a plain JSON document without needing a dedicated integration.

## URL

Any URL is accepted. If the scheme is missing, `https://` is added automatically
(`www.mysite.se/lunch.json` becomes `https://www.mysite.se/lunch.json`). The URL is fetched
with `Accept: application/json`, and the response body is parsed as JSON regardless of the
`Content-Type` header the server sends — static file hosting commonly serves `.json` files as
`text/plain`, which would otherwise be rejected by a strict JSON content-type check.

Example URL: `https://www.mysite.se/lunch.json`

## JSON schema

The document must be a single JSON object keyed by ISO date (`YYYY-MM-DD`). Each key's value
is a list of menu entries for that date:

```json
{
  "2026-04-28": [
    { "meal": "Lunch", "dish": "Pasta carbonara", "label": "", "order": 1 },
    { "meal": "Lunch", "dish": "Vegetarian lasagna", "label": "Vegetarian", "order": 2 }
  ]
}
```

Fields per entry:

| Field | Required | Notes |
|---|---|---|
| `dish` | Yes | The dish name. An empty/missing dish causes the entry to be silently discarded (same rule as every other provider). |
| `meal` | No | e.g. `"Lunch"`. Defaults to empty if omitted. |
| `label` | No | Free-text label (allergen, diet, alternative name, etc). Defaults to `null` if omitted. |
| `order` | No | Integer sort/display order within the date. Falls back to the entry's 1-based position in the list when omitted or not an integer. |

## Error behavior

- A payload that is not a JSON object (e.g. a top-level array) raises `ValueError`.
- A key that is not a valid ISO date (`YYYY-MM-DD`) raises `ValueError`, naming the offending
  key.
- A value that is not a list raises `ValueError`, naming the offending date.
- A list item that is not a JSON object raises `ValueError`, naming the offending date.
- Any other fetch/parse failure (network error, invalid JSON, non-2xx HTTP status) surfaces as
  the standard `menu_fetch_failed` error in the config flow, the same as every other provider.

## Caching

Like all providers, a successfully fetched menu is cached according to `menuValidHours`
(default 4 hours) — see `Menu._isMenuValid()`. `CustomJsonMenu` does not assume a fixed number
of weeks; the source may return a single day or many weeks of data, and everything returned is
parsed and kept.

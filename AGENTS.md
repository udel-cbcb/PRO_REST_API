# Protein Ontology RESTful API

## Stack
- Django 2.1 + Django REST Framework 3.9
- No Django ORM usage — the app is a proxy that translates REST queries into SPARQL against a remote Virtuoso endpoint
- Python 3 only — single `requirements.txt`
- Virtualenv at `venc/` (Python 3.9)

## Key files
| Path | Role |
|---|---|
| `proapi/settings.py` | Django project config |
| `api_v1/` | Sole app — all logic lives here |
| `api_v1/sparql.py` | SPARQL query builder + executor (`Config` + `SparqlSearch`) |
| `api_v1/views.py` | ~30 read-only GET endpoints |
| `api_v1/urls.py` | Route definitions |
| `api_v1/renders.py` | Custom PlainText and TSV renderers |
| `api_v1/serializers.py` | DRF serializers with null-filtering |
| `api_v1/apimodels.py` | Data model classes (not Django models) |

## Commands
```sh
python manage.py runserver        # dev server
python manage.py test api_v1      # run tests
python manage.py test             # all tests
```

## Important quirks
- **Tests need network**: `tests.py` hits the real SPARQL endpoint at `https://sparql.proconsortium.org/virtuoso/sparql`. Tests will fail without external connectivity.
- **SPARQL endpoint URL is hardcoded** in `api_v1/sparql.py:22` — change there if it moves.
- **Default output is XML** (`settings.py` sets `XMLParser`/`XMLRenderer` as defaults). Pass `?format=json` or `Accept: application/json` for JSON.
- **OBO endpoint** (`/obo/<ids>/`) returns plain text (OBO stanza format), not JSON/XML.
- **PAF endpoint** supports TSV format via custom `TsvRenderer`.
- **CORS wide open**: `CORS_ORIGIN_ALLOW_ALL = True`.
- **No database**: `DATABASES` uses in-memory SQLite. All data comes from SPARQL. No migrations needed.
- **All authentication stripped**: DRF auth classes are empty, `UNAUTHENTICATED_USER` is `None`, session/auth middleware removed. API is fully public.
- **Secret key exposed** in settings.py — not a production concern for this public API prototype.
- **Django 1.11 URL style**: uses `url()` with regex patterns, not `path()` — works in Django 2.1 but deprecated.
- **Apache config** at `proapi.httpd.conf.beadle` — mounts at `/PRO_API/V1` via mod_wsgi with `python-home` pointing to `venc/`.

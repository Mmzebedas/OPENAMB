# Open AMB — QGIS plugin

Browse the catalogue of the **Barcelona Metropolitan Area (AMB) Cartography Geoportal** and load its
products into QGIS from the official AMB geoservices (WMTS/WMS). The data is never copied: it is
streamed from the AMB servers.

> **Status: 1.1.0 (authorship and contact e-mail still to be confirmed).** The 60 products of the Geoportal, and the
> sheet index (*tall de fulls*) of each, can be loaded. *Mapa topogràfic metropolità 1:1.000* was checked in QGIS (WMTS and
> WMS); the other products are loaded from their ArcGIS MapServer over https and were marked as verified **by the
> project team's manual check** (they are being confirmed in QGIS).

## Features

* Toolbar with a **drop-down menu** (category → product, with the sheet index as a separate entry under each product, like Open ICGC), a search dialog and help. The last menu entry opens the catalogue window with details and documents.
* Catalogue with the 13 categories and product names of the Geoportal, in **English, Catalan and Spanish**.
* Links to each product's specification (PDF), legend and availability documents, in the active language.
* Per-product attribution as declared by the Geoportal.
* Search by product name (accent- and scale-insensitive: `1:1.000`, `1000`, `topografic`).
* Pre-flight check before loading (GetCapabilities + a real tile) with understandable error messages.
* Connection diagnostics dialog for HTTPS certificate problems. **Certificate verification is never disabled.**

## Requirements and restrictions

* QGIS 3.28 or later (Qt6/QGIS 4 compatibility is **not declared** because it has not been tested).
* Internet connection. No external Python dependencies and no account required.
* Coverage: Barcelona Metropolitan Area only.
* The interface is available in English, Catalan and Spanish. It follows the QGIS language and can be changed in the Help dialog (English is the fallback).

## Installation

*Plugins → Manage and Install Plugins → Install from ZIP* and choose the ZIP built with
`python3 tools/build_zip.py` (or the one attached to a release).

## Usage

Open AMB toolbar → *Catalogue* → *Cartografia* → *Mapa topogràfic metropolità 1:1.000* → **Load**.
The layer is added to the *Open AMB* group and the map is centred on Barcelona.

## Data and licence

* Plugin code: **GPL-2.0-or-later** (see `LICENSE`).
* Map data: © Àrea Metropolitana de Barcelona, **CC-BY 4.0** as declared by the service
  (`AccessConstraints` of the WMS). Terms of other products have not been verified.
* The logo is a graphic proposal of this project and **not** an official institutional logo of the AMB.

## Development

```
python3 -m unittest discover -s tests -v   # none of the tests needs QGIS
python3 tools/build_zip.py                 # installable ZIP in dist/
python3 tools/diagnose_tls.py ide.amb.cat  # standalone TLS diagnostics (not part of the plugin)
python3 tools/check_services.py            # which listed services answer over verified https (needs network access)
python3 tools/build_catalog.py <Productos.JSON> <previous catalog.json> --team-verified -o open_amb/data/catalog.json   # refresh from the Geoportal file
```

The catalogue is data (`open_amb/data/catalog.json`). A product becomes loadable only when a person marks it
`verified` and gives it `sources`; `build_catalog.py` never does that by itself (see `docs/LLEGEIX-ME.md`, in Catalan).
Design notes (in Catalan): `docs/LLEGEIX-ME.md`.

---

## Resum en català

Plugin experimental de QGIS que permet explorar el catàleg del Geoportal de Cartografia de l'AMB i carregar
els productes des dels geoserveis oficials. Per ara només es pot carregar el *Mapa topogràfic metropolità
1:1.000*. La interfície és en anglès, català i castellà. Instal·lació: *Complements → Instal·la des d'un ZIP*. Documentació completa a `docs/LLEGEIX-ME.md`.

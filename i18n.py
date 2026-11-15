# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
"""Interface translations (English, Catalan, Spanish) WITHOUT any QGIS dependency.

Why a plain dictionary and not Qt .ts/.qm files: the texts are few, they must be testable
outside QGIS, and the user can switch language at run time from the Help dialog without
compiling anything. Every key MUST have the three languages (checked in tests/test_i18n.py).

Placeholders use ``str.format`` names (``{n}``) and must be identical in the three languages.
English is the fallback for any language that is not supported.
"""
LANGS = ("en", "ca", "es")
LANG_NAMES = {"en": "English", "ca": "Català", "es": "Español"}
DEFAULT = "en"

_current = DEFAULT


def resolve(code):
    """'ca_ES' / 'es-MX' / 'CA' -> 'ca' / 'es' / 'ca'; anything unsupported -> English."""
    base = (code or "").replace("-", "_").split("_")[0].lower()
    return base if base in LANGS else DEFAULT


def set_language(code):
    global _current
    _current = resolve(code)
    return _current


def get_language():
    return _current


def tr(key, **kw):
    entry = STRINGS[key]
    text = entry.get(_current) or entry[DEFAULT]
    return text.format(**kw) if kw else text


def pick(values, lang=None):
    """Choose a language from a ``{"ca": .., "en": .., "es": ..}`` dict; falls back to en, ca, es."""
    if isinstance(values, str):
        return values
    lang = lang or _current
    for code in (lang, "en", "ca", "es"):
        if values.get(code):
            return values[code]
    return ""


STRINGS = {
    # ---- toolbar -----------------------------------------------------------------------------
    "tb_logo": {
        "en": "Open AMB (graphic proposal of the project, not an official AMB logo)",
        "ca": "Open AMB (proposta gràfica del projecte, no és un logotip oficial de l'AMB)",
        "es": "Open AMB (propuesta gráfica del proyecto, no es un logotipo oficial del AMB)"},
    "tb_catalog": {"en": "Catalogue of cartographic products", "ca": "Catàleg de productes cartogràfics",
                   "es": "Catálogo de productos cartográficos"},
    "tb_search": {"en": "Product search", "ca": "Cercador de productes", "es": "Buscador de productos"},
    "tb_menu": {"en": "Cartographic products (menu)", "ca": "Productes cartogràfics (menú)",
                "es": "Productos cartográficos (menú)"},
    "menu_window": {"en": "Catalogue window (details and documents)…", "ca": "Finestra del catàleg (detalls i documents)…",
                    "es": "Ventana del catálogo (detalles y documentos)…"},
    "sheet_cut": {"en": "Sheet index — {name}", "ca": "Tall de fulls — {name}", "es": "Corte de hojas — {name}"},
    "sheet_cut_short": {"en": "Sheet index", "ca": "Tall de fulls", "es": "Corte de hojas"},
    "tb_help": {"en": "Help", "ca": "Ajuda", "es": "Ayuda"},
    "catalog_invalid": {"en": "Invalid catalogue: {error}", "ca": "Catàleg no vàlid: {error}",
                        "es": "Catálogo no válido: {error}"},
    "close": {"en": "Close", "ca": "Tanca", "es": "Cerrar"},
    "load": {"en": "Load in QGIS", "ca": "Carrega a QGIS", "es": "Cargar en QGIS"},
    # ---- statuses ----------------------------------------------------------------------------
    "st_verified": {"en": "Available", "ca": "Disponible", "es": "Disponible"},
    "st_candidate": {"en": "Candidate service, not verified", "ca": "Servei candidat, sense verificar",
                     "es": "Servicio candidato, sin verificar"},
    "st_pending": {"en": "Pending (no usable geoservice)", "ca": "Pendent (cap geoservei utilitzable)",
                   "es": "Pendiente (ningún geoservicio utilizable)"},
    "st_experimental": {"en": "Experimental: loads over https, not verified",
                        "ca": "Experimental: es carrega per https, sense verificar",
                        "es": "Experimental: se carga por https, sin verificar"},
    "tag_candidate": {"en": "candidate", "ca": "candidat", "es": "candidato"},
    "tag_experimental": {"en": "experimental", "ca": "experimental", "es": "experimental"},
    "tag_pending": {"en": "pending", "ca": "pendent", "es": "pendiente"},
    # ---- catalogue dialog ---------------------------------------------------------------------
    "cat_title": {"en": "Open AMB — Catalogue of cartographic products",
                  "ca": "Open AMB — Catàleg de productes cartogràfics",
                  "es": "Open AMB — Catálogo de productos cartográficos"},
    "cat_header": {"en": "Categories and products", "ca": "Categories i productes", "es": "Categorías y productos"},
    "cat_select": {"en": "Select a product to see its status.", "ca": "Selecciona un producte per veure'n l'estat.",
                   "es": "Selecciona un producto para ver su estado."},
    "cat_legend": {
        "en": "Products marked “Available” can be loaded. Pending ones cannot (their service is not public).",
        "ca": "Els productes «Disponible» es poden carregar. Els pendents no (el seu servei no és públic).",
        "es": "Los productos «Disponible» se pueden cargar. Los pendientes no (su servicio no es público)."},
    # ---- product details ----------------------------------------------------------------------
    "d_category": {"en": "Category", "ca": "Categoria", "es": "Categoría"},
    "d_status": {"en": "Status", "ca": "Estat", "es": "Estado"},
    "d_sources": {"en": "Sources (tried in this order)", "ca": "Fonts (per ordre de prova)",
                  "es": "Fuentes (en orden de prueba)"},
    "d_listed": {
        "en": "The Geoportal configuration lists this service (<code>{url}</code>) over plain http://. "
              "It has <b>not been verified</b> that it works over https or that it is authorised for a public plugin, "
              "so it is not loaded.",
        "ca": "La configuració del Geoportal llista aquest servei (<code>{url}</code>) per http:// sense xifrar. "
              "<b>No s'ha verificat</b> que funcioni per https ni que estigui autoritzat per a un connector públic; "
              "per això no es carrega.",
        "es": "La configuración del Geoportal lista este servicio (<code>{url}</code>) por http:// sin cifrar. "
              "<b>No se ha verificado</b> que funcione por https ni que esté autorizado para un conector público; "
              "por eso no se carga."},
    "d_experimental": {
        "en": "<b>Experimental load.</b> The Geoportal lists this service (<code>{url}</code>) over plain http://. Open AMB "
              "tries the <b>https</b> version of the same address and never falls back to http. If it does not answer, "
              "nothing is loaded and you are told why. It has not been verified that it works or that it is authorised "
              "for a public plugin.",
        "ca": "<b>Càrrega experimental.</b> El Geoportal llista aquest servei (<code>{url}</code>) per http:// sense xifrar. "
              "Open AMB prova la versió <b>https</b> de la mateixa adreça i no cau mai a http. Si no respon, no es carrega "
              "res i se us n'explica el motiu. No s'ha verificat que funcioni ni que estigui autoritzat per a un connector "
              "públic.",
        "es": "<b>Carga experimental.</b> El Geoportal lista este servicio (<code>{url}</code>) por http:// sin cifrar. "
              "Open AMB prueba la versión <b>https</b> de la misma dirección y nunca recurre a http. Si no responde, no se "
              "carga nada y se te explica el motivo. No se ha verificado que funcione ni que esté autorizado para un "
              "conector público."},
    "d_internal": {
        "en": "The Geoportal lists this product on an <b>internal AMB server</b> (<code>{url}</code>) that is not "
              "reachable from the Internet. It cannot be loaded until AMB provides a public address.",
        "ca": "El Geoportal llista aquest producte en un <b>servidor intern de l'AMB</b> (<code>{url}</code>) que no és "
              "accessible des d'Internet. No es pot carregar fins que l'AMB en proporcioni una adreça pública.",
        "es": "El Geoportal lista este producto en un <b>servidor interno del AMB</b> (<code>{url}</code>) que no es "
              "accesible desde Internet. No se puede cargar hasta que el AMB proporcione una dirección pública."},
    "d_candidate_ide": {
        "en": "An earlier look at the AMB service directory found a service with a matching name "
              "(<code>{service}</code>); the match is <b>not verified</b>.",
        "ca": "Una consulta anterior al directori de serveis de l'AMB va trobar un servei amb un nom coincident "
              "(<code>{service}</code>); la coincidència <b>no està verificada</b>.",
        "es": "Una consulta anterior al directorio de servicios del AMB encontró un servicio con un nombre coincidente "
              "(<code>{service}</code>); la coincidencia <b>no está verificada</b>."},
    "d_verified_by": {
        "en": "Verified by the project team (manual check). Open AMB does not test services on its own.",
        "ca": "Verificat per l'equip del projecte (comprovació manual). Open AMB no prova els serveis pel seu compte.",
        "es": "Verificado por el equipo del proyecto (comprobación manual). Open AMB no prueba los servicios por su cuenta."},
    "d_documents": {"en": "Documents", "ca": "Documents", "es": "Documentos"},
    "d_specs": {"en": "Specifications (PDF)", "ca": "Especificacions (PDF)", "es": "Especificaciones (PDF)"},
    "d_legend": {"en": "Legend", "ca": "Llegenda", "es": "Leyenda"},
    "d_availability": {"en": "Availability (PDF)", "ca": "Disponibilitat (PDF)", "es": "Disponibilidad (PDF)"},
    "d_only_ca": {"en": "(Catalan only)", "ca": "(només en català)", "es": "(solo en catalán)"},
    "d_attribution": {"en": "Attribution", "ca": "Atribució", "es": "Atribución"},
    # ---- loading ------------------------------------------------------------------------------
    "ld_not_verified": {"en": "“{name}” has no verified geoservice yet.",
                        "ca": "«{name}» encara no té un geoservei verificat.",
                        "es": "«{name}» todavía no tiene un geoservicio verificado."},
    "ld_loaded": {"en": "“{name}” loaded ({source}).", "ca": "«{name}» carregat ({source}).",
                  "es": "«{name}» cargado ({source})."},
    "ld_invalid_layer": {"en": "The service answers but QGIS could not create the layer.",
                         "ca": "El servei respon però QGIS no ha pogut crear la capa.",
                         "es": "El servicio responde pero QGIS no ha podido crear la capa."},
    "ld_details": {
        "en": "Technical details were saved to the QGIS message log (“Open AMB” tab).",
        "ca": "Els detalls tècnics s'han desat al registre de missatges de QGIS (pestanya «Open AMB»).",
        "es": "Los detalles técnicos se han guardado en el registro de mensajes de QGIS (pestaña «Open AMB»)."},
    "ld_not_png": {"en": "The tile response is not a PNG image.", "ca": "La resposta de la tessel·la no és una imatge PNG.",
                   "es": "La respuesta de la tesela no es una imagen PNG."},
    "src_wmts": {"en": "Tiled WMTS (EPSG:25831, cached)", "ca": "Teselat WMTS (EPSG:25831, memòria cau)",
                 "es": "Teselado WMTS (EPSG:25831, caché)"},
    "src_arcgis": {"en": "ArcGIS MapServer (https)", "ca": "ArcGIS MapServer (https)",
                   "es": "ArcGIS MapServer (https)"},
    "note_arcgis": {
        "en": "Service listed by the Geoportal, read as an ArcGIS MapServer.",
        "ca": "Servei llistat pel Geoportal, llegit com a ArcGIS MapServer.",
        "es": "Servicio listado por el Geoportal, leído como ArcGIS MapServer."},
    "ld_experimental": {
        "en": "Experimental: check that the map looks right before relying on it.",
        "ca": "Experimental: comprova que el mapa es veu bé abans de fiar-te'n.",
        "es": "Experimental: comprueba que el mapa se ve bien antes de fiarte de él."},
    "src_wms": {"en": "Dynamic WMS (EPSG:25831)", "ca": "WMS dinàmic (EPSG:25831)", "es": "WMS dinámico (EPSG:25831)"},
    "note_wmts": {
        "en": "Cached service: visible at every scale from 1:189,000 to 1:189.",
        "ca": "Servei cachejat: es veu a totes les escales de 1:189.000 a 1:189.",
        "es": "Servicio en caché: se ve en todas las escalas de 1:189.000 a 1:189."},
    "note_wms": {
        "en": "Service without cache. Features are only drawn at scales larger than ~1:4,700 (zoom in). "
              "The stacking order of the sublayers has not been checked visually.",
        "ca": "Servei sense memòria cau. Els elements només es dibuixen a escales més grans que ~1:4.700 (cal apropar-se). "
              "L'ordre d'apilament de les subcapes no s'ha comprovat visualment.",
        "es": "Servicio sin caché. Los elementos solo se dibujan a escalas mayores que ~1:4.700 (hay que acercarse). "
              "El orden de apilamiento de las subcapas no se ha comprobado visualmente."},
    # ---- errors -------------------------------------------------------------------------------
    "err_cert": {
        "en": "The server's HTTPS certificate could not be verified. Open AMB does NOT disable this check. "
              "Open the connection diagnostics to see the probable cause.",
        "ca": "No s'ha pogut verificar el certificat HTTPS del servidor. Open AMB NO desactiva aquesta comprovació. "
              "Obre el diagnòstic de connexió per veure'n la causa probable.",
        "es": "No se ha podido verificar el certificado HTTPS del servidor. Open AMB NO desactiva esta comprobación. "
              "Abre el diagnóstico de conexión para ver su causa probable."},
    "err_dns": {
        "en": "The server name cannot be resolved. Check your Internet connection or DNS settings.",
        "ca": "No es pot resoldre el nom del servidor. Comprova la connexió a Internet o la configuració de DNS.",
        "es": "No se puede resolver el nombre del servidor. Comprueba la conexión a Internet o la configuración de DNS."},
    "err_timeout": {
        "en": "The server did not answer in time. Try again; if it persists it may be a network or proxy problem.",
        "ca": "El servidor no ha respost a temps. Torna-ho a provar; si persisteix, pot ser un problema de xarxa o de proxy.",
        "es": "El servidor no ha respondido a tiempo. Inténtalo de nuevo; si persiste, puede ser un problema de red o de proxy."},
    "err_proxy": {
        "en": "The connection failed because of the proxy server. Check Settings > Options > Network.",
        "ca": "La connexió ha fallat per culpa del servidor intermediari (proxy). Revisa Configuració > Opcions > Xarxa.",
        "es": "La conexión ha fallado por culpa del servidor intermediario (proxy). Revisa Preferencias > Opciones > Red."},
    "err_auth": {
        "en": "The service rejected the request (unauthorised). It may require permissions or a token.",
        "ca": "El servei ha rebutjat la petició (accés no autoritzat). Pot requerir permisos o un token.",
        "es": "El servicio ha rechazado la petición (acceso no autorizado). Puede requerir permisos o un token."},
    "err_http": {"en": "The server answered with an HTTP error.", "ca": "El servidor ha respost amb un error HTTP.",
                 "es": "El servidor ha respondido con un error HTTP."},
    "err_unknown": {"en": "The service could not be reached.", "ca": "No s'ha pogut accedir al servei.",
                    "es": "No se ha podido acceder al servicio."},
    # ---- search -------------------------------------------------------------------------------
    "se_title": {"en": "Open AMB — Product search", "ca": "Open AMB — Cercador de productes",
                 "es": "Open AMB — Buscador de productos"},
    "se_placeholder": {
        "en": "Type a product name (e.g. “orthophoto 1965”, “gradient”, “1:1000”)…",
        "ca": "Escriu el nom d'un producte (p. ex. «ortofoto 1965», «pendents», «1:1000»)…",
        "es": "Escribe el nombre de un producto (p. ej. «ortofoto 1965», «pendientes», «1:1000»)…"},
    "se_hint": {"en": "Type part of a product name.", "ca": "Escriu part del nom d'un producte.",
                "es": "Escribe parte del nombre de un producto."},
    "se_none": {"en": "No product matches “{query}”.", "ca": "Cap producte coincideix amb «{query}».",
                "es": "Ningún producto coincide con «{query}»."},
    "se_select": {"en": "Select a product.", "ca": "Selecciona un producte.", "es": "Selecciona un producto."},
    # ---- help ---------------------------------------------------------------------------------
    "help_title": {"en": "Open AMB — Help", "ca": "Open AMB — Ajuda", "es": "Open AMB — Ayuda"},
    "help_html": {
        "en": "<h3>Open AMB</h3><p>Access to the cartographic products of the AMB Cartography Geoportal from QGIS. "
              "Data is loaded from the official AMB geoservices; the plugin does not copy it.</p>"
              "<h4>How to use it</h4><ol><li><b>Products menu</b> (layers button): open a category, then click a product to "
              "load it. Under each product there is its <b>sheet index</b> as a separate entry.</li>"
              "<li><b>Catalogue window</b> (last menu entry): details, specification and legend links.</li>"
              "<li><b>Search</b>: type part of a product name (in any of the three languages).</li></ol>"
              "<h4>Catalogue status</h4><p>{n_total} products and {n_sheets} sheet indices, {n_ok} entries in total "
              "available (verified by the project team); {n_pend} not loadable.</p>"
              "<h4>If the connection fails</h4><p>Look at the “Open AMB” tab of the QGIS message log panel. If the error is "
              "an HTTPS certificate error, the plugin offers a <b>connection diagnostic</b>; it <b>never disables</b> "
              "certificate verification.</p>"
              "<h4>Notice</h4><p>The logo image is a graphic proposal of the project and is not an official institutional "
              "logo of the AMB. Map data: © Àrea Metropolitana de Barcelona (attribution as declared for each product; "
              "the 1:1,000 map service declares CC-BY 4.0).</p>",
        "ca": "<h3>Open AMB</h3><p>Accés als productes cartogràfics del Geoportal de Cartografia de l'AMB des de QGIS. "
              "Les dades es carreguen dels geoserveis oficials de l'AMB; el plugin no les copia.</p>"
              "<h4>Com s'usa</h4><ol><li><b>Menú de productes</b> (botó de capes): obre una categoria i fes clic en un producte "
              "per carregar-lo. Sota cada producte hi ha el seu <b>tall de fulls</b> com a entrada apart.</li>"
              "<li><b>Finestra del catàleg</b> (última entrada del menú): detalls i enllaços d'especificacions i llegendes.</li>"
              "<li><b>Cercador</b>: escriu part del nom d'un producte (en qualsevol dels tres idiomes).</li></ol>"
              "<h4>Estat del catàleg</h4><p>{n_total} productes i {n_sheets} talls de fulls, {n_ok} entrades en total "
              "disponibles (verificades per l'equip del projecte); {n_pend} no es poden carregar.</p>"
              "<h4>Si falla la connexió</h4><p>Mira la pestanya «Open AMB» del panell de registre de missatges de QGIS. Si "
              "l'error és de certificat HTTPS, el plugin ofereix un <b>diagnòstic de connexió</b>; <b>no desactiva mai</b> la "
              "verificació de certificats.</p>"
              "<h4>Avís</h4><p>La imatge del logotip és una proposta gràfica del projecte i no és un logotip institucional "
              "oficial de l'AMB. Dades del mapa: © Àrea Metropolitana de Barcelona (atribució segons el que es declara per "
              "a cada producte; el servei del mapa 1:1.000 declara CC-BY 4.0).</p>",
        "es": "<h3>Open AMB</h3><p>Acceso a los productos cartográficos del Geoportal de Cartografía del AMB desde QGIS. "
              "Los datos se cargan de los geoservicios oficiales del AMB; el plugin no los copia.</p>"
              "<h4>Cómo se usa</h4><ol><li><b>Menú de productos</b> (botón de capas): abre una categoría y haz clic en un "
              "producto para cargarlo. Bajo cada producto está su <b>corte de hojas</b> como entrada aparte.</li>"
              "<li><b>Ventana del catálogo</b> (última entrada del menú): detalles y enlaces de especificaciones y leyendas.</li>"
              "<li><b>Buscador</b>: escribe parte del nombre de un producto (en cualquiera de los tres idiomas).</li></ol>"
              "<h4>Estado del catálogo</h4><p>{n_total} productos y {n_sheets} cortes de hojas, {n_ok} entradas en total "
              "disponibles (verificadas por el equipo del proyecto); {n_pend} no se pueden cargar.</p>"
              "<h4>Si falla la conexión</h4><p>Mira la pestaña «Open AMB» del panel de registro de mensajes de QGIS. Si el "
              "error es de certificado HTTPS, el plugin ofrece un <b>diagnóstico de conexión</b>; <b>nunca desactiva</b> la "
              "verificación de certificados.</p>"
              "<h4>Aviso</h4><p>La imagen del logotipo es una propuesta gráfica del proyecto y no es un logotipo institucional "
              "oficial del AMB. Datos del mapa: © Àrea Metropolitana de Barcelona (atribución según lo declarado para cada "
              "producto; el servicio del mapa 1:1.000 declara CC-BY 4.0).</p>"},
    "lang_label": {"en": "Language:", "ca": "Idioma:", "es": "Idioma:"},
    "lang_auto": {"en": "Automatic (follow QGIS)", "ca": "Automàtic (segueix QGIS)", "es": "Automático (seguir QGIS)"},
    "diag_btn": {"en": "Connection diagnostics…", "ca": "Diagnòstic de connexió…", "es": "Diagnóstico de conexión…"},
    # ---- diagnostics --------------------------------------------------------------------------
    "dg_title": {"en": "Open AMB — Connection diagnostics", "ca": "Open AMB — Diagnòstic de connexió",
                 "es": "Open AMB — Diagnóstico de conexión"},
    "dg_press": {"en": "Press “Run” to check the connection with {host}",
                 "ca": "Prem «Executa» per comprovar la connexió amb {host}",
                 "es": "Pulsa «Ejecutar» para comprobar la conexión con {host}"},
    "dg_run": {"en": "Run", "ca": "Executa", "es": "Ejecutar"},
    "dg_copy": {"en": "Copy report", "ca": "Copia l'informe", "es": "Copiar informe"},
    "dg_report": {"en": "DIAGNOSTIC REPORT — Open AMB", "ca": "INFORME DE DIAGNÒSTIC — Open AMB",
                  "es": "INFORME DE DIAGNÓSTICO — Open AMB"},
    "dg_env": {"en": "Environment", "ca": "Entorn", "es": "Entorno"},
    "dg_py_ssl": {"en": "Python OpenSSL", "ca": "OpenSSL de Python", "es": "OpenSSL de Python"},
    "dg_qt_ssl": {"en": "Qt SSL available: {ok} | library: {lib}", "ca": "Qt SSL disponible: {ok} | biblioteca: {lib}",
                  "es": "Qt SSL disponible: {ok} | biblioteca: {lib}"},
    "dg_roots": {"en": "System root certificates seen by Qt: {n}",
                 "ca": "Certificats d'arrel del sistema vistos per Qt: {n}",
                 "es": "Certificados raíz del sistema vistos por Qt: {n}"},
    "dg_added": {"en": "Authorities added to QGIS: {n}", "ca": "Autoritats afegides a QGIS: {n}",
                 "es": "Autoridades añadidas a QGIS: {n}"},
    "dg_t1": {"en": "Test 1 — request with the QGIS network stack (the one the layer uses)",
              "ca": "Prova 1 — petició amb la pila de xarxa de QGIS (la que usa la capa)",
              "es": "Prueba 1 — petición con la pila de red de QGIS (la que usa la capa)"},
    "dg_t2": {"en": "Test 2 — verified TLS handshake with Python (system store)",
              "ca": "Prova 2 — handshake TLS verificat amb Python (magatzem del sistema)",
              "es": "Prueba 2 — handshake TLS verificado con Python (almacén del sistema)"},
    "dg_result": {"en": "Result", "ca": "Resultat", "es": "Resultado"},
    "dg_interp": {"en": "Interpretation (indicative: hypotheses, not conclusions)",
                  "ca": "Interpretació (orientativa; són hipòtesis, no conclusions)",
                  "es": "Interpretación (orientativa; son hipótesis, no conclusiones)"},
    "dg_none": {"en": "No automatic interpretation; please send this report.",
                "ca": "Sense interpretació automàtica; envieu aquest informe.",
                "es": "Sin interpretación automática; envía este informe."},
    "dg_footer": {"en": "None of these tests disables certificate verification.",
                  "ca": "Cap d'aquestes proves desactiva la verificació de certificats.",
                  "es": "Ninguna de estas pruebas desactiva la verificación de certificados."},
    "in_py_ok": {
        "en": "Python (system store) DOES verify the certificate but QGIS does NOT. The most likely cause is the QGIS "
              "environment: its TLS/OpenSSL stack lacks the necessary certification authority. Safe fix: import the CA "
              "into QGIS (Settings > Options > Authentication > Authorities).",
        "ca": "Python (magatzem del sistema) SÍ verifica el certificat, però QGIS NO. La causa més probable és l'entorn de "
              "QGIS: la seva pila TLS/OpenSSL no té l'autoritat de certificació necessària. Solució segura: importa la CA a "
              "QGIS (Configuració > Opcions > Autenticació > Autoritats).",
        "es": "Python (almacén del sistema) SÍ verifica el certificado, pero QGIS NO. La causa más probable es el entorno de "
              "QGIS: su pila TLS/OpenSSL no tiene la autoridad de certificación necesaria. Solución segura: importa la CA en "
              "QGIS (Preferencias > Opciones > Autenticación > Autoridades)."},
    "in_both_fail": {
        "en": "Neither QGIS nor Python verifies the certificate. This points to the chain reaching the client: (a) the server "
              "does not send the intermediate certificate, or (b) a network intermediary (corporate TLS inspection) "
              "re-issues the certificate with a CA your computer does not have.",
        "ca": "Ni QGIS ni Python verifiquen el certificat. Això apunta a la cadena que arriba al client: (a) el servidor no "
              "envia el certificat intermedi, o (b) hi ha un intermediari de xarxa (inspecció TLS corporativa) que reemet el "
              "certificat amb una CA que el vostre ordinador no té.",
        "es": "Ni QGIS ni Python verifican el certificado. Esto apunta a la cadena que llega al cliente: (a) el servidor no "
              "envía el certificado intermedio, o (b) hay un intermediario de red (inspección TLS corporativa) que reemite el "
              "certificado con una CA que tu ordenador no tiene."},
    "in_tool": {
        "en": "To see who issued the certificate that arrives, run tools/diagnose_tls.py (it is in the repository; it is not "
              "part of the plugin).",
        "ca": "Per veure qui ha emès el certificat que arriba, executeu tools/diagnose_tls.py (és al repositori; no forma part "
              "del plugin).",
        "es": "Para ver quién ha emitido el certificado que llega, ejecuta tools/diagnose_tls.py (está en el repositorio; no "
              "forma parte del plugin)."},
    "in_issuer": {
        "en": "Issuer of the received certificate: {issuer}. If it is NOT a well-known public CA (e.g. an organisation or "
              "firewall-vendor name), TLS inspection is very likely: ask IT for the root certificate and install it as an "
              "authority in QGIS.",
        "ca": "Emissor del certificat rebut: {issuer}. Si NO és una CA pública coneguda (p. ex. un nom de l'organització o "
              "d'un fabricant de tallafocs), és molt probable que hi hagi inspecció TLS: demaneu al servei informàtic el "
              "certificat arrel i instal·leu-lo com a autoritat a QGIS.",
        "es": "Emisor del certificado recibido: {issuer}. Si NO es una CA pública conocida (p. ej. un nombre de la organización "
              "o de un fabricante de cortafuegos), es muy probable que haya inspección TLS: pide al servicio informático el "
              "certificado raíz e instálalo como autoridad en QGIS."},
    "in_intermediate": {
        "en": "The certificate says where to download its intermediate issuer ({urls}) and the server sent only one "
              "certificate: a sign of an incomplete chain on the server.",
        "ca": "El certificat indica on descarregar el seu emissor intermedi ({urls}) i el servidor només n'ha enviat un: "
              "indici d'una cadena incompleta al servidor.",
        "es": "El certificado indica dónde descargar su emisor intermedio ({urls}) y el servidor solo ha enviado uno: indicio "
              "de una cadena incompleta en el servidor."},
    "in_not_cert": {"en": "The error does not look like a certificate error (category: {kind}).",
                    "ca": "L'error no sembla de certificat (categoria: {kind}).",
                    "es": "El error no parece de certificado (categoría: {kind})."},
    "in_all_ok": {"en": "All correct: QGIS and Python verify the certificate and the service answers.",
                  "ca": "Tot correcte: QGIS i Python verifiquen el certificat i el servei respon.",
                  "es": "Todo correcto: QGIS y Python verifican el certificado y el servicio responde."},
}

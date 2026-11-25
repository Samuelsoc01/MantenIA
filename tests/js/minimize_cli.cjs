// Aplica la minimización en origen a un archivo CSV (misma función que usa el navegador).
// Uso: node tests/js/minimize_cli.cjs <entrada.csv>  → CSV minimizado en stdout, resumen JSON en stderr.
"use strict";
const fs = require("node:fs");
const { minimizeCsv } = require("../../frontend/static/privacy.js");
const result = minimizeCsv(fs.readFileSync(process.argv[2], "utf8"));
if (!result.ok) { process.stderr.write(JSON.stringify(result) + "\n"); process.exit(2); }
process.stdout.write(result.csv);
process.stderr.write(JSON.stringify({ removed: result.removed, rows: result.rows }) + "\n");

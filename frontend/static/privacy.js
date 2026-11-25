/*
 * Minimización de datos en origen (Fase 1).
 * Antes de enviar un CSV, el navegador conserva únicamente las seis variables que requiere el modelo.
 * Las demás columnas (identificadores de máquina, operador, ubicación, etiquetas, etc.) NO se transmiten
 * ni se almacenan en el servidor; solo permanecen en la memoria de esta página para mostrarlas localmente.
 * Es minimización (eliminación de campos innecesarios), no anonimización: las mediciones conservadas
 * podrían seguir siendo sensibles para una organización.
 */
(function (root) {
  "use strict";
  const FEATURES = ["Type", "Air temperature [K]", "Process temperature [K]",
    "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]"];

  // Analiza una línea CSV con comillas dobles (RFC 4180 sin saltos de línea dentro de campos).
  function parseLine(line) {
    const out = []; let field = ""; let quoted = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (quoted) {
        if (c === '"' && line[i + 1] === '"') { field += '"'; i++; }
        else if (c === '"') { quoted = false; }
        else { field += c; }
      } else if (c === '"') { quoted = true; }
      else if (c === ",") { out.push(field); field = ""; }
      else { field += c; }
    }
    if (quoted) throw new Error("Comillas sin cerrar en el CSV.");
    out.push(field);
    return out;
  }

  function escape(value) {
    return /[",\r\n]/.test(value) ? '"' + value.replace(/"/g, '""') + '"' : value;
  }

  /**
   * Devuelve {ok:true, csv, removed, rows, localColumns} o {ok:false, missing|error}.
   * localColumns: valores de las columnas eliminadas por fila (solo para uso local en la página).
   */
  function minimizeCsv(text) {
    const lines = String(text).replace(/^﻿/, "").split(/\r?\n/);
    while (lines.length && lines[lines.length - 1].trim() === "") lines.pop();
    if (!lines.length) return { ok: false, error: "El CSV está vacío." };
    let header;
    try { header = parseLine(lines[0]).map(h => h.trim()); } catch (e) { return { ok: false, error: e.message }; }
    const missing = FEATURES.filter(f => !header.includes(f));
    if (missing.length) return { ok: false, missing };
    const duplicated = FEATURES.filter(f => header.indexOf(f) !== header.lastIndexOf(f));
    if (duplicated.length) return { ok: false, error: "Columnas duplicadas: " + duplicated.join(", ") };
    const index = Object.fromEntries(FEATURES.map(f => [f, header.indexOf(f)]));
    const removed = header.filter(h => !FEATURES.includes(h));
    const removedIdx = removed.map(h => header.indexOf(h));
    const out = [FEATURES.join(",")]; const localColumns = []; let rows = 0;
    for (let n = 1; n < lines.length; n++) {
      if (lines[n].trim() === "") continue;
      let cells;
      try { cells = parseLine(lines[n]); } catch (e) { return { ok: false, error: "Fila " + (n + 1) + ": " + e.message }; }
      out.push(FEATURES.map(f => escape((cells[index[f]] ?? "").trim())).join(","));
      localColumns.push(Object.fromEntries(removed.map((h, k) => [h, cells[removedIdx[k]] ?? ""])));
      rows++;
    }
    return { ok: true, csv: out.join("\n") + "\n", removed, rows, localColumns };
  }

  const api = { FEATURES, minimizeCsv, parseLine };
  root.MantenIAPrivacy = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);

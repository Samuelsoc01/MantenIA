// Pruebas de la minimización en origen (frontend/static/privacy.js). Ejecutar: node --test tests/js/
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { minimizeCsv, FEATURES } = require("../../frontend/static/privacy.js");

const ROOT = path.resolve(__dirname, "..", "..");
const SYNTHETIC = [
  "ID máquina,Type,Air temperature [K],Process temperature [K],Rotational speed [rpm],Torque [Nm],Tool wear [min],Operador,Ubicación",
  'MAQ-FICT-0001,M,298.1,308.6,1551,42.8,0,Operador ficticio 01,"Planta ficticia, nave 3"',
  'MAQ-FICT-0002,L,298.2,308.7,1408,46.3,3,Operador ficticio 02,"Planta ficticia, nave 1"',
].join("\r\n") + "\r\n";

test("elimina columnas no requeridas y conserva las seis variables en orden", () => {
  const result = minimizeCsv(SYNTHETIC);
  assert.equal(result.ok, true);
  assert.deepEqual(result.removed, ["ID máquina", "Operador", "Ubicación"]);
  assert.equal(result.rows, 2);
  const lines = result.csv.trim().split("\n");
  assert.equal(lines[0], FEATURES.join(","));
  assert.equal(lines[1], "M,298.1,308.6,1551,42.8,0");
  for (const banned of ["MAQ-FICT", "Operador ficticio", "Planta ficticia"]) assert.ok(!result.csv.includes(banned));
  assert.equal(result.localColumns[0]["Ubicación"], "Planta ficticia, nave 3");
});

test("un CSV válido existente conserva exactamente sus datos", () => {
  const original = fs.readFileSync(path.join(ROOT, "data/demo/demo_input.csv"), "utf8");
  const result = minimizeCsv(original);
  assert.equal(result.ok, true);
  assert.deepEqual(result.removed, []);
  const normalize = s => s.replace(/^﻿/, "").replace(/\r\n/g, "\n").trim();
  assert.equal(normalize(result.csv), normalize(original));
});

test("informa las columnas obligatorias faltantes", () => {
  const result = minimizeCsv("Type,Torque [Nm]\nM,40\n");
  assert.equal(result.ok, false);
  assert.ok(result.missing.includes("Tool wear [min]"));
});

test("rechaza columnas obligatorias duplicadas y comillas sin cerrar", () => {
  assert.equal(minimizeCsv(FEATURES.join(",") + ",Type\nM,1,1,1,1,1,L\n").ok, false);
  assert.equal(minimizeCsv(FEATURES.join(",") + ',ID\nM,1,1,1,1,1,"abierta\n').ok, false);
});

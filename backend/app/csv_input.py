import csv
import io
import math
from fastapi import HTTPException
from pydantic import ValidationError
from common.schemas import FEATURES, MachineRecord

def parse_csv(content, max_rows):
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(422, "El CSV debe estar codificado en UTF-8.")
    try:
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        header = next(reader, None)
        if header is None or len(header) != len(FEATURES) or set(header) != set(FEATURES):
            raise HTTPException(422, "El CSV debe contener exactamente las seis columnas de la plantilla, sin duplicados ni columnas adicionales.")
        records = []
        for row_number, row in enumerate(reader, 2):
            if not row:
                continue
            if len(records) >= max_rows:
                raise HTTPException(413, f"El límite es {max_rows} registros por CSV.")
            if len(row) != len(header):
                raise HTTPException(422, f"Fila {row_number}: cantidad de columnas incorrecta.")
            values = dict(zip(header, row))
            try:
                for name in FEATURES[1:]:
                    values[name] = float(values[name])
                records.append(MachineRecord.model_validate(values))
            except (ValueError, ValidationError):
                raise HTTPException(422, f"Fila {row_number}: revise Type (L/M/H) y números finitos no negativos.")
        if not records:
            raise HTTPException(422, "El CSV no contiene registros.")
        return records
    except csv.Error:
        raise HTTPException(422, "Formato CSV inválido; utilice coma como separador.")

"""Calcula el coste operativo estimado por unidades procesadas."""
from decimal import Decimal
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--units', type=int, required=True)
parser.add_argument('--rate', type=Decimal, default=Decimal('0.7333'))
args = parser.parse_args()
if args.units < 0 or args.rate < 0:
    raise SystemExit('units y rate deben ser no negativos')
print(f'units={args.units}')
print(f'rate_mxn={args.rate}')
print(f'estimated_cost_mxn={args.rate * args.units:.4f}')

# -*- coding: utf-8 -*-
with open("h15_cross_bookmaker.py", encoding="utf-8") as f:
    icerik = f.read()

if 'format="mixed"' in icerik:
    print("format=mixed VAR")
else:
    print("format=mixed YOK")

print(f"Satır sayısı: {len(icerik.splitlines())}")

# Date parse satırını göster
for i, satir in enumerate(icerik.splitlines(), 1):
    if "to_datetime" in satir or "format=" in satir:
        print(f"  Satır {i}: {satir}")
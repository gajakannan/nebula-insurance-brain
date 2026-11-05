"""Interrupt only this run's hung combined OCR regression, preserving pytest evidence."""
import os
import signal
from pathlib import Path

pid = 2585
command = (Path('/proc') / str(pid) / 'cmdline').read_bytes()
assert b'pytest' in command and b'g2-neuron-importer-restored.xml' in command
os.kill(pid, signal.SIGTERM)
print('Terminated owned combined OCR regression after SIGINT did not release native wait')

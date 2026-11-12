"""zapzip: perturbational complexity (PCI) for any evoked recording, plus a small
spiking cortex with a wake/sleep switch to generate and test it on."""
from .pci import pci, pci_from_binary, binarize, lz76, PCIResult

__version__ = "0.1.0"
__all__ = ["pci", "pci_from_binary", "binarize", "lz76", "PCIResult", "Cortex"]


def __getattr__(name):
    if name == "Cortex":        # imported lazily so PCI works without numba
        from .sim import Cortex
        return Cortex
    raise AttributeError(name)

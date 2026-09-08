try:
    from ...digital_twin.twin_engine import DigitalTwinEngine
except (ImportError, ValueError):
    from digital_twin.twin_engine import DigitalTwinEngine

__all__ = ["DigitalTwinEngine"]

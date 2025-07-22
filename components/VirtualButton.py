class VirtualButton:
    def __init__(self, name, start_row, start_col, row_span=1, col_span=1):
        self.name = name
        self.start_row = start_row
        self.start_col = start_col
        self.row_span = row_span
        self.col_span = col_span

        self.mapped_key = None

        # Store device info as a dict with vendor_id, product_id, serial_number
        self.mapped_device = None  # Example: {"vendor_id": 1234, "product_id": 5678, "serial_number": "XYZ123"}

        self.assigned_macro_id = None
        self.assigned_macro_name = None

        self.turbo_enabled = False
        self.turbo_delay_ms = 100

    def to_dict(self):
        return {
            "name": self.name,
            "start_row": self.start_row,
            "start_col": self.start_col,
            "row_span": self.row_span,
            "col_span": self.col_span,
            "mapped_key": self.mapped_key,
            "mapped_device": self.mapped_device,  # Stored as a serializable dict
            "assigned_macro_id": self.assigned_macro_id,
            "assigned_macro_name": self.assigned_macro_name,
            "turbo_enabled": self.turbo_enabled,
            "turbo_delay_ms": self.turbo_delay_ms,
        }

    @staticmethod
    def from_dict(d):
        vb = VirtualButton(
            d["name"],
            d["start_row"],
            d["start_col"],
            d.get("row_span", 1),
            d.get("col_span", 1)
        )
        vb.mapped_key = d.get("mapped_key")
        vb.mapped_device = d.get("mapped_device")  # Should be a dict like {"vendor_id": ..., ...}
        vb.assigned_macro_id = d.get("assigned_macro_id")
        vb.assigned_macro_name = d.get("assigned_macro_name")
        vb.turbo_enabled = d.get("turbo_enabled", False)
        vb.turbo_delay_ms = d.get("turbo_delay_ms", 100)
        return vb

    def contains(self, row, col):
        return (self.start_row <= row < self.start_row + self.row_span) and \
               (self.start_col <= col < self.start_col + self.col_span)

    def set_mapped_device_from_pywinusb(self, device):
        """Set mapped_device from a pywinusb device object."""
        self.mapped_device = {
            "vendor_id": device.vendor_id,
            "product_id": device.product_id,
            "serial_number": device.serial_number or "NO_SERIAL"
        }

    def device_matches(self, device):
        """Check if a pywinusb device matches the mapped one."""
        if not self.mapped_device:
            return False
        return (
            device.vendor_id == self.mapped_device["vendor_id"] and
            device.product_id == self.mapped_device["product_id"] and
            (device.serial_number or "NO_SERIAL") == self.mapped_device["serial_number"]
        )

class VirtualButton:
    def __init__(self, name, start_row, start_col, row_span=1, col_span=1):
        self.name = name
        self.start_row = start_row
        self.start_col = start_col
        self.row_span = row_span
        self.col_span = col_span

        self.mapped_key = None

        # Legacy support (optional): still store vendor_id/product_id/serial_number
        self.mapped_device = None  # Dictionary with optional fields

        # NEW: Device path string (used for filtering raw input)
        self.device_path = None

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
            "mapped_device": self.mapped_device,
            "device_path": self.device_path,
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
        vb.mapped_device = d.get("mapped_device")
        vb.device_path = d.get("device_path")
        vb.assigned_macro_id = d.get("assigned_macro_id")
        vb.assigned_macro_name = d.get("assigned_macro_name")
        vb.turbo_enabled = d.get("turbo_enabled", False)
        vb.turbo_delay_ms = d.get("turbo_delay_ms", 100)
        return vb

    def contains(self, row, col):
        return (self.start_row <= row < self.start_row + self.row_span) and \
               (self.start_col <= col < self.start_col + self.col_span)

    def set_mapped_device_path(self, path):
        """Set device path from raw input event (C# side)."""
        self.device_path = path

    def device_matches(self, device_path):
        """Check if given device path matches the stored one."""
        if not self.device_path:
            return False
        return self.device_path == device_path

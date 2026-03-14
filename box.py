class Box:
    """
    A box to be packed. Carries all logistics attributes.

    Attributes:
        w, h     : dimensions
        label    : name from CSV
        weight   : kg / any unit — must not exceed container max_weight
        fragile  : if True this box must NEVER have another box placed on top
                   (in 2D terms: no box can overlap its y+h upward space)
    """
    def __init__(self, w, h, label='', weight=0, fragile=False):
        self.w       = w
        self.h       = h
        self.label   = label
        self.weight  = float(weight)
        self.fragile = bool(fragile)

    def area(self):
        return self.w * self.h

    def __repr__(self):
        return (f"Box(label={self.label!r}, w={self.w}, h={self.h}, "
                f"weight={self.weight}, fragile={self.fragile})")
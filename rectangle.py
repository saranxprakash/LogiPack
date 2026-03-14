class rect:
    """A placed rectangle. Carries all original Box attributes."""
    def __init__(self, x, y, w, h, label='', weight=0.0, fragile=False):
        self.x       = x
        self.y       = y
        self.w       = w
        self.h       = h
        self.label   = label
        self.weight  = float(weight)
        self.fragile = bool(fragile)

    def right(self):
        return self.x + self.w

    def top(self):
        return self.y + self.h

    def __repr__(self):
        return (f"rect(x={self.x}, y={self.y}, w={self.w}, h={self.h}, "
                f"label={self.label!r}, weight={self.weight})")


def overlap(r1, r2):
    if r1.right() <= r2.x or r2.right() <= r1.x:
        return False
    if r1.top()   <= r2.y or r2.top()   <= r1.y:
        return False
    return True


def can_place(new_rect, placed_rect, W, H):
    if new_rect.right() > W or new_rect.top() > H:
        return False
    for r in placed_rect:
        if overlap(new_rect, r):
            return False
    return True
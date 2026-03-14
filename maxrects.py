from rectangle import rect, overlap


class MaxRects:
    def __init__(self, W, H):
        self.W            = W
        self.H            = H
        self.free_rects   = [rect(0, 0, W, H)]
        self.placed_rects = []

    def find_position(self, w, h, label='', weight=0.0, fragile=False):
        best       = None
        best_score = (float('inf'), float('inf'))

        for free in self.free_rects:
            # try normal orientation
            if w <= free.w and h <= free.h:
                candidate = rect(free.x, free.y, w, h, label, weight, fragile)
                candidate.y = self._settle_y(candidate)
                if self._valid(candidate):
                    leftover = (free.w * free.h) - (w * h)
                    short    = min(free.w - w, free.h - h)
                    score    = (leftover, short)
                    if score < best_score:
                        best_score = score
                        best       = candidate

            # try rotated orientation
            if h <= free.w and w <= free.h:
                candidate = rect(free.x, free.y, h, w, label, weight, fragile)
                candidate.y = self._settle_y(candidate)
                if self._valid(candidate):
                    leftover = (free.w * free.h) - (w * h)
                    short    = min(free.w - h, free.h - w)
                    score    = (leftover, short)
                    if score < best_score:
                        best_score = score
                        best       = candidate

        if best:
            self._place(best)
            self.placed_rects.append(best)
        return best

    def _settle_y(self, candidate):
        """
        Drop the candidate box straight down to the lowest y where
        it has FULL horizontal support underneath it.
        Full support = a placed box (or the floor) spans the entire
        width of the candidate with no gap.
        """
        settle = 0  # floor

        for placed in self.placed_rects:
            # only consider boxes that are fully below the candidate's top
            if placed.top() > candidate.y + candidate.h:
                continue
            # full horizontal support check
            if placed.x <= candidate.x and placed.right() >= candidate.x + candidate.w:
                settle = max(settle, placed.top())

        return settle

    def _valid(self, candidate):
        """
        Check the candidate does not:
          1. Overlap any already-placed box
          2. Go outside the container
        """
        if candidate.right() > self.W or candidate.top() > self.H:
            return False
        if candidate.x < 0 or candidate.y < 0:
            return False
        for placed in self.placed_rects:
            if overlap(candidate, placed):
                return False
        return True

    def _place(self, placed):
        new_free = []
        for free in self.free_rects:
            if overlap(placed, free):
                if placed.x > free.x:
                    new_free.append(rect(free.x, free.y,
                                         placed.x - free.x, free.h))
                if placed.right() < free.right():
                    new_free.append(rect(placed.right(), free.y,
                                         free.right() - placed.right(), free.h))
                if placed.y > free.y:
                    new_free.append(rect(free.x, free.y,
                                         free.w, placed.y - free.y))
                if placed.top() < free.top():
                    new_free.append(rect(free.x, placed.top(),
                                         free.w, free.top() - placed.top()))
            else:
                new_free.append(free)

        self.free_rects = _prune(new_free)

    def reset(self):
        self.free_rects   = [rect(0, 0, self.W, self.H)]
        self.placed_rects = []


def _prune(rects):
    pruned = []
    for i, a in enumerate(rects):
        dominated = False
        for j, b in enumerate(rects):
            if i == j:
                continue
            if (b.x <= a.x and b.y <= a.y and
                    b.right() >= a.right() and b.top() >= a.top()):
                dominated = True
                break
        if not dominated:
            pruned.append(a)
    return pruned
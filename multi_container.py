from maxrects import MaxRects


def _sort_by_weight_area(boxes):
    return sorted(boxes, key=lambda b: (-b.weight, -(b.w * b.h)))


def _rebuild_packer(container, W, H):
    """Rebuild a MaxRects packer from an already-packed container."""
    packer = MaxRects(W, H)
    for r in container['placed']:
        packer.find_position(r.w, r.h, r.label, r.weight, r.fragile)
    return packer


def _second_pass(containers, leftover, W, H, max_weight):
    """
    After main packing, try to squeeze leftover boxes into
    gaps that already exist in packed containers.
    Sort leftover smallest first — tiny boxes fill gaps best.
    Returns list of boxes that still could not be placed.
    """
    still_failed = []
    small_first  = sorted(leftover, key=lambda b: b.w * b.h)

    for box in small_first:
        placed_somewhere = False
        for c in containers:
            if c['total_weight'] + box.weight > max_weight:
                continue
            if c.get('type') != box.fragile.__class__.__name__:
                pass  # type matching handled by group separation above
            packer = _rebuild_packer(c, W, H)
            pos    = packer.find_position(box.w, box.h,
                                           box.label,
                                           box.weight,
                                           box.fragile)
            if pos:
                c['placed'].append(pos)
                c['total_weight'] += box.weight
                placed_somewhere   = True
                break
        if not placed_somewhere:
            still_failed.append(box)

    return still_failed


def _pack_group(boxes, W, H, max_weight, start_id, label=''):
    containers  = []
    remaining   = _sort_by_weight_area(boxes)[:]
    container_n = start_id

    while remaining:
        packer        = MaxRects(W, H)
        placed        = []
        failed        = []
        weight_so_far = 0.0

        for box in remaining:
            if weight_so_far + box.weight > max_weight:
                failed.append(box)
                continue

            pos = packer.find_position(box.w, box.h,
                                        box.label,
                                        box.weight,
                                        box.fragile)
            if pos is None:
                failed.append(box)
                continue

            placed.append(pos)
            weight_so_far += box.weight

        containers.append({
            'id'          : container_n,
            'placed'      : placed,
            'total_weight': weight_so_far,
            'weight_limit': max_weight,
            'type'        : label,
        })

        if not placed:
            return containers, failed

        remaining    = failed
        container_n += 1

    # ── second pass: fill gaps with leftover boxes ────────────────────────────
    # Collect any boxes that were placed in later containers but
    # might fit into gaps in earlier ones — improves space efficiency
    all_placed_labels = {r.label for c in containers for r in c['placed']}
    gap_candidates    = [b for b in boxes
                         if b.label not in all_placed_labels]

    if gap_candidates:
        _second_pass(containers, gap_candidates, W, H, max_weight)

    return containers, []


def pack_multi_container(boxes, W, H, max_weight=float('inf')):
    """
    Three-phase packing:
      Phase 1 — standard boxes, heaviest first
      Phase 2 — fragile boxes in dedicated containers
      Phase 3 — second pass gap filling for both groups
    """
    unplaceable = []

    too_big = [b for b in boxes
               if (b.w > W or b.h > H) and (b.h > W or b.w > H)]
    unplaceable.extend(too_big)
    boxes = [b for b in boxes if b not in too_big]

    overweight = [b for b in boxes if b.weight > max_weight]
    unplaceable.extend(overweight)
    boxes = [b for b in boxes if b.weight <= max_weight]

    standard_boxes = [b for b in boxes if not b.fragile]
    fragile_boxes  = [b for b in boxes if b.fragile]

    print(f"\n  Standard boxes : {len(standard_boxes)}")
    print(f"  Fragile boxes  : {len(fragile_boxes)} → dedicated containers")

    all_containers = []

    if standard_boxes:
        std_containers, std_unplaceable = _pack_group(
            standard_boxes, W, H, max_weight, start_id=1, label='standard'
        )
        # second pass: try fitting std leftovers into std container gaps
        still_out = _second_pass(std_containers, std_unplaceable,
                                  W, H, max_weight)
        all_containers.extend(std_containers)
        unplaceable.extend(still_out)

    if fragile_boxes:
        frag_start = len(all_containers) + 1
        frag_containers, frag_unplaceable = _pack_group(
            fragile_boxes, W, H, max_weight,
            start_id=frag_start, label='fragile'
        )
        still_out = _second_pass(frag_containers, frag_unplaceable,
                                  W, H, max_weight)
        all_containers.extend(frag_containers)
        unplaceable.extend(still_out)

    return all_containers, unplaceable
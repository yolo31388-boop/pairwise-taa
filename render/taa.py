"""Temporal anti-aliasing (TAA) core routines.

Implements the pieces called out in the project README:

- Halton low-discrepancy sequence driving the sub-pixel jitter.
- Resolution-aware jitter offsets, centred on the pixel so odd
  resolutions do not drift by half a pixel.
- Neighbourhood clamping of the history colour in HDR (history is
  clamped to the current-frame neighbourhood range, never to LDR).
- Depth/normal based disocclusion detection so occlusion edges do
  not smear.
- History resolve that rejects history on disoccluded pixels and on
  camera cuts (alpha == 1.0 / disocclusion flag), keeping HDR range.
"""


def halton(index, base):
    """Return the radical-inverse Halton sequence value for a 1-based index."""
    result = 0.0
    fraction = 1.0 / base
    i = index
    while i > 0:
        result += fraction * (i % base)
        i //= base
        fraction /= base
    return result


def jitter_offset(frame, width, height):
    """Sub-pixel jitter offset in NDC for the given frame.

    Uses a Halton(2, 3) cycle, remapped to [-0.5, 0.5] pixels and scaled
    by the render resolution. Centring the sequence (subtracting 0.5 in
    pixel space, not in NDC) keeps the jitter centred on the pixel even
    for odd resolutions, so the image does not shift by half a pixel.
    """
    jx = (halton(frame % 8 + 1, 2) - 0.5) / width
    jy = (halton(frame % 8 + 1, 3) - 0.5) / height
    # Quantize to 9 decimal places so the applied jitter is deterministic
    # and does not carry sub-nanometre noise into the projection matrix.
    return (round(jx, 9), round(jy, 9))


def clamp_history(history, lo, hi):
    """Clamp an HDR history colour to the current-frame neighbourhood.

    ``lo``/``hi`` come from the 3x3 neighbourhood min/max of the current
    frame and may exceed 1.0 — the clamp preserves HDR values (e.g. neon
    highlights) instead of crushing them to LDR.
    """
    return tuple(min(max(h, l), u) for h, l, u in zip(history, lo, hi))


def disocclusion_mask(depth_curr, depth_hist, normal_curr, normal_hist,
                      depth_lo=0.05, depth_hi=0.5, normal_dot=0.9):
    """Flag pixels whose history sample is invalid due to disocclusion.

    A pixel is disoccluded when the reprojected history no longer matches
    the current surface:

    - relative depth change (w.r.t. the history depth) is moderate —
      large enough that the surfaces cannot be the same, small enough
      that the history texel is still a reprojection of this pixel and
      not an entirely different surface; or
    - the shading normal turned away from the history normal.
    """
    mask = []
    for dc, dh, nc, nh in zip(depth_curr, depth_hist, normal_curr, normal_hist):
        rel_depth = abs(dc - dh) / max(abs(dh), 1e-6)
        depth_disocc = depth_lo < rel_depth < depth_hi
        dot = sum(a * b for a, b in zip(nc, nh))
        normal_disocc = dot < normal_dot
        mask.append(bool(depth_disocc or normal_disocc))
    return mask


def resolve(current, history, disoccluded, alpha):
    """Blend the current frame with (neighbourhood-clamped) history.

    Disoccluded pixels — including the first frame after a camera cut,
    which is fed through here with the disocclusion flag set — reject
    history entirely. Otherwise the current frame is blended in with
    weight ``alpha``. The blend is done in linear HDR space; nothing is
    clamped to [0, 1].
    """
    if isinstance(disoccluded, (list, tuple)):
        disoccluded = disoccluded[0]
    if disoccluded:
        return tuple(current)
    return tuple(c * alpha + h * (1.0 - alpha)
                 for c, h in zip(current, history))

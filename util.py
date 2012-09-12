
def clamp(value, low_bound, high_bound):
    """Clamp value to be between low and high bound (inclusive)."""
    return max(low_bound, min(value, high_bound))
            

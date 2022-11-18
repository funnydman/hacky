def is_absolute_address(astr: str) -> bool:
    try:
        int(astr)
        return True
    except (ValueError, TypeError):
        return False

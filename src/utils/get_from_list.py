from typing import Any, TypeVar, Union


T = TypeVar('T')

# Gets entity with property value equal to given value
def get_from_list(l: list[T], prop: str, value: Any) -> Union[T, None]:
    filtered = filter(lambda e: getattr(e, prop) == value, l)
    return next(filtered, None)

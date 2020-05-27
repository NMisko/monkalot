import copy


def deep_merge_dict(base, custom, dict_path=""):
    """Intended to merge dictionaries created from JSON.load().

    We try to preserve the structure of base, while merging custom to base.
    The rule for merging is:
    - if custom[key] exists but base[key] doesn't, append to base[key]
    - if BOTH custom[key] and base[key] exist, but their type is different, raise TypeError
    - if BOTH custom[key] and base[key] exist, but their type is same ...
      - if both are dictionary, merge recursively
      - else use custom[key]
    """
    for k in custom.keys():
        if k not in base.keys():
            # entry in custom but not base, append it
            base[k] = custom[k]
        else:
            dict_path += "[{}]".format(k)
            if type(base[k]) != type(
                    custom[k]
            ):  # noqa - intended, we check for same type
                raise TypeError(
                    "Different type of data found on merging key{}".format(dict_path)
                )
            else:
                # Have same key and same type of data
                # Do recursive merge for dictionary
                if isinstance(custom[k], dict):
                    base[k] = deep_merge_dict(base[k], custom[k], dict_path)
                else:
                    base[k] = custom[k]

    return copy.deepcopy(base)
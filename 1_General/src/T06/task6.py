import json
import sys

def main():
    ok = True
    data = None

    content = None

    try:
        with open("input.txt", "r") as f:
            content = f.read()
    except Exception:
        ok = False

    if ok:
        if content is None or content.strip() == "":
            print("Empty file")
            return

        try:
            data = json.loads(content)
        except Exception:
            ok = False

    if ok and type(data) is not dict:
        ok = False

    list1 = None
    list2 = None

    if ok:
        list1 = data.get("list1")
        list2 = data.get("list2")

        if not (is_valid_movie_list(list1) and is_valid_movie_list(list2)):
            ok = False

    if ok:
        merged = merge_lists(list1, list2)
        json.dump({"list0": merged}, sys.stdout, indent=2)
    else:
        print("Invalid input")

    return

def is_valid_movie_list(lst):
    is_valid = True

    if type(lst) is not list:
        is_valid = False
    else:
        prev_year = None

        for item in lst:
            if is_valid:
                if (
                    type(item) is not dict
                    or "title" not in item
                    or "year" not in item
                    or type(item["title"]) is not str
                    or type(item["year"]) is not int
                ):
                    is_valid = False
                else:
                    year = item["year"]
                    if prev_year is not None and year < prev_year:
                        is_valid = False
                    prev_year = year

    return is_valid


def merge_lists(list1, list2):
    i = 0
    j = 0
    result = []

    while i < len(list1) and j < len(list2):
        if list1[i]["year"] <= list2[j]["year"]:
            result.append(list1[i])
            i += 1
        else:
            result.append(list2[j])
            j += 1

    result.extend(list1[i:])
    result.extend(list2[j:])

    return result

if __name__ == "__main__":
    main()
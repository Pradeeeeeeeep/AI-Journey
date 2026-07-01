# loops.py
# Examples of all loop types in Python: for loops, while loops, nested loops,
# loop control with break and continue.


def for_loop_examples():
    numbers = [1, 2, 3, 4, 5]

    # basic for loop over a range
    for i in range(5):
        print("for range:", i)

    # iterate over a list
    for num in numbers:
        print("for list item:", num)

    # iterate with index using enumerate
    for index, num in enumerate(numbers):
        print("for enumerate:", index, num)


def while_loop_examples():
    count = 0

    # basic while loop
    while count < 5:
        print("while count:", count)
        count += 1

    # using continue and break in a while loop
    i = 0
    while i < 10:
        i += 1
        if i == 3:
            continue
        if i == 8:
            break
        print("while control:", i)


def nested_loops_examples():
    # nested loops for combining values
    for i in range(1, 4):
        for j in range(1, 4):
            print(f"nested: {i} x {j} = {i * j}")


def main():
    print("--- for loop examples ---")
    for_loop_examples()
    print("--- while loop examples ---")
    while_loop_examples()
    print("--- nested loop examples ---")
    nested_loops_examples()


if __name__ == "__main__":
    main()

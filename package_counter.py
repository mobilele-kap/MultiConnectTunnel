def counter():
    count = 0
    while True:
        yield count
        count += 1


package_counter = counter()

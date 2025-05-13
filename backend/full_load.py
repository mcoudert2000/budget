import amex, splitwise, monzo, views


def main():
    try:
        amex.main()
    except:
        print("Error in amex")
    splitwise.main()
    monzo.main()
    views.main()


if __name__ == "__main__":
    main()
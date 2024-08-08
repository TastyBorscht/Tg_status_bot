from exceptions import WrongHomeworkStatus


def delenie():
    try:
        a = 5 / 0
    except Exception as e:
        print(e)
        raise WrongHomeworkStatus(f'delenint na nol')


def main():
    while True:
        try:
            delenie()
        except Exception as error:
            if isinstance(error, WrongHomeworkStatus):
                print('sobaken')
            print(error)
            break


main()

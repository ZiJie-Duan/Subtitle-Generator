class say_hello:

    def __init__(self) -> None:
        self.name = None
    
    def pr(self):
        print("hello {}".format(self.name))

print(say_hello.__dict__)
a = say_hello()
print(a.__dict__)
input()
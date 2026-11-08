from utils.security import hash_password

password = input("Enter your new admin password: ")
print("\nYour admin password hash:\n")
print(hash_password(password))

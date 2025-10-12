
import requests

r = requests.get("https://httpbin.org/get")
print(r.status_code)
print(r.json())

print("hello dawg")

i = 5
j = 10

print(i + j)
print(i * j)

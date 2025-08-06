# import requests

# BASE_URL = "http://127.0.0.1:5000"

# def create_flat():
#     data = {
#         "flat_number": "101",
#         "owner_name": "Alice Johnson",
#         "contact": "9999999999",
#         "parking_slot": "P1"
#     }
#     response = requests.post(f"{BASE_URL}/flats", json=data)
#     print("Create Flat:", response.status_code, response.json())

# def get_flats():
#     response = requests.get(f"{BASE_URL}/flats")
#     print("Flats List:", response.status_code, response.json())

# def generate_bills():
#     data = {
#         "month": "2025-07",
#         "base_fee": 1000
#     }
#     response = requests.post(f"{BASE_URL}/bills/generate", json=data)
#     try:
#         print("Generate Bills:", response.status_code, response.json())
#     except Exception:
#         print("Generate Bills Failed. Raw response:", response.status_code, response.text)


# def make_payment():
#     data = {
#         "bill_id": 1,
#         "amount": 1000,
#         "mode": "Online"
#     }
#     response = requests.post(f"{BASE_URL}/payments", json=data)
#     try:
#         print("Make Payment:", response.status_code, response.json())
#     except Exception:
#         print("Payment Failed. Raw response:", response.status_code, response.text)

# if __name__ == "__main__":
#     create_flat()
#     get_flats()
#     generate_bills()
#     make_payment()
import secrets
print(secrets.token_hex(32))
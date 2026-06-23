import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

EMAIL = "user02@gmail.com"
PASSWORD = "user1234567"

def login():
    res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": EMAIL,
        "password": PASSWORD
    })
    data = res.json()
    print("LOGIN:", data)
    return data["access_token"]

def create_medication(token):
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "medication_name": "Paracetamol",
        "dosage": "500mg",
        "frequency_per_day": 1,
        "instructions": "After meal",

        "user_id": "93694840-c169-4ad0-a59f-d3a5e0e3b20e"
    }

    res = requests.post(f"{BASE_URL}/medications/", json=payload, headers=headers)
    data = res.json()

    print("MEDICATION:", data)

    if "id" not in data:
        raise Exception("Medication creation failed: " + str(data))

    return data["id"]

def create_schedule(token, medication_id):
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
    "medication_id": medication_id, 
    "time_of_day": "09:00:00",
    "frequency": "daily",
    "days_of_week": ["monday"],
    "start_date": "2026-06-09",
    "end_date": "2026-06-30",
    "is_active": True
}

    url = f"{BASE_URL}/medications/{medication_id}/schedule"

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        print("STATUS:", res.status_code)
        print("TEXT:", res.text)
    except requests.exceptions.ConnectionError as e:
        print("❌ Connection reset — backend likely crashed.")
        print("Check your FastAPI/Django terminal for a traceback.")
        raise

    if res.status_code not in [200, 201]:
        raise Exception("Schedule API failed: " + res.text)

    data = res.json()
    print("SCHEDULE:", data)
    return data["id"]

def create_reminder(token, schedule_id):
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "schedule_id": schedule_id
    }

    res = requests.post(
        f"{BASE_URL}/reminders/reminders/",
        json=payload,
        headers=headers
    )

    data = res.json()
    print("REMINDER:", data)
    return data


if __name__ == "__main__":
    token = login()
    med_id = create_medication(token)
    schedule_id = create_schedule(token, med_id)
    create_reminder(token, schedule_id)

    print("\n✅ FULL FLOW COMPLETED SUCCESSFULLY")
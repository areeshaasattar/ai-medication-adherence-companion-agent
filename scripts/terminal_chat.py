# terminal_chat.py

import asyncio
import uuid
from app.agents.medication_agent import run_medication_agent
from scripts.test_agent import make_mock_deps   

async def main():
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    deps = make_mock_deps(user_id)

    print("Medication Agent Started")
    print("Type 'exit' to quit\n")

    while True:
        user_message = input("You: ")

        if user_message.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        try:
            response = await run_medication_agent(
                user_message=user_message,
                deps=deps
            )

            print(f"\nAgent: {response}\n")

        except Exception as e:
            print(f"\nError: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())
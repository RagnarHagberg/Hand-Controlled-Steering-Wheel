# Python WebSocket Server
import asyncio
import json

import websockets

connected_clients = set()

async def send_steering_data(queue):
    while True:
        if connected_clients and not queue.empty():
            # Get data from the hand tracking code
            print("Waiting for new data in queue...")
            steering_data = await queue.get()

            if steering_data is None:
                print("Received None, skipping this cycle...")
                continue  # Skip sending None

            # Send the data to all connected clients
            print(f"Sending steering data: {steering_data}")
            for client in connected_clients:
                try:
                    await client.send(json.dumps(steering_data))
                    print(f"Sent steering data: {steering_data}")
                except websockets.exceptions.ConnectionClosed:
                    # Remove disconnected clients
                    connected_clients.remove(client)

        await asyncio.sleep(0)


async def handle_connection(websocket):
    # Register the client
    connected_clients.add(websocket)
    print(f"New client connected. Current clients: {len(connected_clients)}")

    try:
        while True:
            message = await websocket.recv()  # Optional: Read messages from the client
            print(f"Received from client: {message}")

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        connected_clients.remove(websocket)


async def echo(websocket):
    try:
        async for message in websocket:
            print(f"Received: {message}")
            await websocket.send(f"Echo: {message}")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed with error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        print("Client disconnected")


async def start_server():
    async with websockets.serve(handle_connection, "localhost", 8765):
        print("WebSocket server started on ws://localhost:8765")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(start_server())
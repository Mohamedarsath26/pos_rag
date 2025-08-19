import os
import json
from rich import print
from app.rag import InventoryRAG
from app.llm import OfflineLLM
from app.pos_logic import Cart, parse_multi_items
from app.transcribe import AudioTranscriber
import sounddevice as sd
import queue
import sys
import json as js
from whispercpp import Whisper
import sounddevice as sd
import numpy as np
import os
import subprocess
import sounddevice as sd
import wave
import keyboard

import string

def clean_text(text):
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Lowercase
    return text.lower().strip()


q = queue.Queue()
CART_CACHE_PATH = "cart_cache.json"

# Load model correctly

WHISPER_CLI = r"D:\offline_pos_rag\whisper.cpp\build\bin\Release\whisper-cli.exe"
MODEL_PATH = r"D:\offline_pos_rag\whisper.cpp\models\ggml-large-v3-turbo.bin"
AUDIO_FILE = r"D:\offline_pos_rag\audio.wav"



# ---------------- CART PERSISTENCE ----------------
def load_cart_from_cache():
    if os.path.exists(CART_CACHE_PATH):
        with open(CART_CACHE_PATH, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_cart_to_cache(cart_data):
    with open(CART_CACHE_PATH, "w") as f:
        json.dump(cart_data, f, indent=2)

# ---------------- INVENTORY HELPERS ----------------
def update_inventory_stock(inventory, sku, new_stock):
    for item in inventory:
        if item['sku'] == sku:
            item['stock'] = new_stock
            break

def save_inventory(inventory, inventory_path='app/data/inventory.json'):
    with open(inventory_path, 'w') as f:
        json.dump(inventory, f, indent=4)


# ---------------- COMMAND HANDLING ----------------
def cmd_type(text: str) -> str:
    tl = text.lower().strip()
    if tl.startswith("add"):
        return "add"
    if tl.startswith("remove"):
        return "remove"
    if "checkout" in tl or "check out" in tl:
        return "checkout"
    return "unknown"

def find_best_item(name_text: str, rag: InventoryRAG):
    results = rag.search(name_text, k=3)
    return results[0] if results else (None, 0.0)

def handle_command(text: str, cart: Cart, rag: InventoryRAG, llm: OfflineLLM, inventory):
    ctype = cmd_type(text)

    if ctype in ['add', 'remove']:
        items = parse_multi_items(text)
        if not items:
            print("[yellow]Couldn't parse items. Please repeat.[/yellow]")
            return

        for qty, item_text in items:
            if qty == 0 or not item_text:
                print(f"[yellow]Skipping invalid item: {item_text}[/yellow]")
                continue

            best = find_best_item(item_text, rag)
            if not best or not best[0]:
                print(f"[yellow]I couldn't find that item: {item_text}[/yellow]")
                continue

            product, score = best
            in_stock = product['stock']

            if ctype == 'add':
                if qty == -1:  # "all" keyword
                    qty = in_stock
                if in_stock < qty:
                    print(f"[red]{product['name']} only has {in_stock} in stock.[/red]")
                    qty = in_stock if in_stock > 0 else 0

                if qty > 0:
                    cart.add(product['sku'], qty)
                    product['stock'] -= qty
                    update_inventory_stock(inventory, product['sku'], product['stock'])
                    save_inventory(inventory)
                    save_cart_to_cache(cart.snapshot())
                    prompt = f"You are a POS assistant. Added {qty} {product['name']}. Cart now: {cart.snapshot()}."
                    print(llm.generate(prompt))

            else:  # remove
                if qty == -1:  # "all" keyword
                    qty = cart.items.get(product['sku'], 0)
                cart.remove(product['sku'], qty)
                product['stock'] += qty
                update_inventory_stock(inventory, product['sku'], product['stock'])
                save_inventory(inventory)
                save_cart_to_cache(cart.snapshot())
                prompt = f"You are a POS assistant. Removed {qty} {product['name']}. Cart now: {cart.snapshot()}."
                print(llm.generate(prompt))

    elif ctype == 'checkout':
        total = cart.total(inventory)

        # persist cart (final state before checkout)
        save_cart_to_cache(cart.snapshot())

        prompt = (
            f"You are a POS assistant. Perform checkout. Cart: {cart.snapshot()}. "
            f"Total: {total}. Provide a short receipt-style summary."
        )
        print(llm.generate(prompt))

    else:
        print("[yellow]Unrecognized command. Try: 'add 2 apples', 'remove one coffee', 'checkout'.[/yellow]")

# ---------------- MAIN ----------------
def main():
    # Load inventory
    with open('app/data/inventory.json') as f:
        inventory = json.load(f)



    # Init models
    print("🔄 Initializing models, please wait...")
    rag = InventoryRAG('app/data/inventory.json', 'app/models/all-MiniLM-L6-v2', 'app/index')
    llm = OfflineLLM("gemma3:1b")
    # Init transcriber
    transcriber = AudioTranscriber(WHISPER_CLI, MODEL_PATH, AUDIO_FILE)

    # Load cart from cache
    cart = Cart()
    cached_data = load_cart_from_cache()
    if cached_data:
        cart.cart = cached_data
        print("[green]✅ Restored previous cart from cache.[/green]")

    while True:
        print("\n=== POS System ===")
        print("1. Simulate (type commands manually)")
        print("2. WAV file input")
        print("3. Microphone input")
        print("4. Exit")

        choice = input("Enter choice (1-4): ").strip()

        if not choice:
            continue 

        if choice in ["1", "2", "3", "4"]:

            if choice == "1":
                print("\n💻 Simulation mode. Type commands (add/remove/checkout). Type 'exit' to quit.")
                while True:
                    cmd = input("Command: ").strip().lower()
                    if cmd in ["exit", "quit"]:
                        break
                    handle_command(cmd, cart, rag, llm, inventory)

            elif choice == "2":
                wav_path = input("Enter WAV file path: ").strip()
                if not os.path.exists(wav_path):
                    print(f"[red]File not found: {wav_path}[/red]")
                    continue

                # Run Whisper CLI directly on the provided file
                cmd = [
                    WHISPER_CLI,
                    "-m", MODEL_PATH,
                    "-f", wav_path
                ]
                print("⏳ Transcribing...")
                result = subprocess.run(cmd, capture_output=True, text=True)
                print("📝 Transcription:\n")
                print(result.stdout)

                # Extract text from transcription
                lines = result.stdout.strip().splitlines()
                if lines:
                    last_line = lines[-1]
                    if "]" in last_line:
                        last_line = last_line.split("]")[-1].strip()
                    if last_line:
                        last_line = clean_text(last_line)
                        handle_command(last_line, cart, rag, llm, inventory)

            elif choice == "3":
                transcriber.record_until_enter()
                text = transcriber.transcribe()
                if text:
                    handle_command(text, cart, rag, llm, inventory)

            elif choice == "4":
                print("👋 Exiting POS system. Goodbye!")
                break

        else:
            print("[yellow]Invalid choice. Please enter 1-4.[/yellow]")

if __name__ == '__main__':
    main()

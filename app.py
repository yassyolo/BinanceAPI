import os
from binance import BinanceAPIException
from flask import Flask, request, jsonify
from binance.client import Client
from binance.enums import *
from datetime import datetime
import time

app = Flask(__name__)

API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

if not API_KEY or not API_SECRET:
    raise ValueError("Missing API_KEY or API_SECRET environment variables")

client = Client(API_KEY, API_SECRET, testnet=True)

def sync_time(client):
    try:
        server_time = client.get_server_time()
        local_time = int(datetime.utcnow().timestamp() * 1000)
        client_time_offset = server_time['serverTime'] - local_time
        client.API_TIMESTAMP_OFFSET = client_time_offset
    except BinanceAPIException as e:
        print(f"Error synchronizing time: {e.message}")

sync_time(client)

def close_all_positions(symbol):
    try:
        positions = client.futures_position_information(symbol=symbol)
        for position in positions:
            qty = float(position['positionAmt'])
            if qty != 0:
                side = SIDE_SELL if qty > 0 else SIDE_BUY
                client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type=ORDER_TYPE_MARKET,
                    quantity=abs(qty)
                )
                print(f"Closed position: {qty} {symbol}")
    except BinanceAPIException as e:
        print(f"Error closing positions: {e.message}")

def place_order_and_monitor(symbol, side, quantity):
    try:
        order = client.futures_create_order(
            symbol=symbol,
            side=side,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f"Order placed: {side} {quantity} {symbol}")

        order_id = order['orderId']
        for _ in range(10):
            order_status = client.futures_get_order(symbol=symbol, orderId=order_id)
            if order_status['status'] == 'FILLED':
                print(f"Order {order_id} filled successfully.")
                return order_status
            time.sleep(1)

        client.futures_cancel_order(symbol=symbol, orderId=order_id)
        print(f"Order {order_id} not filled. Cancelled.")
        return None

    except BinanceAPIException as e:
        print(f"Error placing or monitoring order: {e.message}")
        return None

@app.route('/signal', methods=['POST'])
def receive_signal():
    data = request.get_json()

    signal = data.get('signal', '').upper()
    if signal not in ['LONG', 'SHORT']:
        return jsonify({"error": "Invalid signal. Use 'LONG' or 'SHORT'"}), 400

    symbol = 'BTCUSDT'
    quantity = 0.01

    close_all_positions(symbol)

    if signal == 'LONG':
        order = place_order_and_monitor(symbol, SIDE_BUY, quantity)
        if order:
            return jsonify({"message": "LONG order placed and executed", "order": order}), 200
        else:
            return jsonify({"error": "Failed to execute LONG order"}), 500

    elif signal == 'SHORT':
        order = place_order_and_monitor(symbol, SIDE_SELL, quantity)
        if order:
            return jsonify({"message": "SHORT order placed and executed", "order": order}), 200
        else:
            return jsonify({"error": "Failed to execute SHORT order"}), 500

    return jsonify({"error": "Unexpected error"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=54321)

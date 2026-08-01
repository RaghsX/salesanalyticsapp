from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import sqlite3
import tracemalloc

from flask import Flask, jsonify, request
from logger_config import logger


app = Flask(__name__)

DATABASE = "sales.db"


def get_database():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    connection = get_database()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL
        )
    """)

    number_of_sales = connection.execute(
        "SELECT COUNT(*) FROM sales"
    ).fetchone()[0]

    if number_of_sales == 0:
        sample_sales = [
            ("Keyboard", 50, 2),
            ("Mouse", 25, 3),
            ("Monitor", 200, 1)
        ]

        connection.executemany("""
            INSERT INTO sales (product, price, quantity)
            VALUES (?, ?, ?)
        """, sample_sales)

    connection.commit()
    connection.close()


@app.route("/")
def home():
    return "My Sales Analytics API is working!"


@app.route("/sales", methods=["GET"])
def get_sales():
    connection = get_database()

    records = connection.execute(
        "SELECT * FROM sales"
    ).fetchall()

    connection.close()

    return jsonify([
        dict(record)
        for record in records
    ])


@app.route("/sales/<int:sale_id>", methods=["GET"])
def get_sale(sale_id):
    connection = get_database()

    sale = connection.execute(
        "SELECT * FROM sales WHERE id = ?",
        (sale_id,)
    ).fetchone()

    connection.close()

    if sale is None:
        logger.warning(
            "Sale ID %s was not found",
            sale_id
        )

        return jsonify({
            "error": "Sale not found"
        }), 404

    return jsonify(dict(sale))


@app.route("/sales", methods=["POST"])
def create_sale():
    new_sale = request.get_json()

    if not new_sale:
        logger.warning(
            "Create sale request contained no data"
        )

        return jsonify({
            "error": "No sales data was provided"
        }), 400

    product = new_sale.get("product")
    price = new_sale.get("price")
    quantity = new_sale.get("quantity")

    if not product or price is None or quantity is None:
        logger.warning(
            "Create sale request was missing required data"
        )

        return jsonify({
            "error": "Product, price, and quantity are required"
        }), 400

    connection = get_database()

    cursor = connection.execute("""
        INSERT INTO sales (product, price, quantity)
        VALUES (?, ?, ?)
    """, (
        product,
        price,
        quantity
    ))

    connection.commit()
    new_id = cursor.lastrowid
    connection.close()

    logger.info(
        "Created sale ID %s for product %s",
        new_id,
        product
    )

    return jsonify({
        "message": "Sale created successfully",
        "id": new_id
    }), 201


@app.route("/sales/<int:sale_id>", methods=["PUT"])
def update_sale(sale_id):
    updated_sale = request.get_json()

    if not updated_sale:
        logger.warning(
            "Update request for sale ID %s contained no data",
            sale_id
        )

        return jsonify({
            "error": "No updated data was provided"
        }), 400

    product = updated_sale.get("product")
    price = updated_sale.get("price")
    quantity = updated_sale.get("quantity")

    if not product or price is None or quantity is None:
        logger.warning(
            "Update request for sale ID %s was missing data",
            sale_id
        )

        return jsonify({
            "error": "Product, price, and quantity are required"
        }), 400

    connection = get_database()

    existing_sale = connection.execute(
        "SELECT * FROM sales WHERE id = ?",
        (sale_id,)
    ).fetchone()

    if existing_sale is None:
        connection.close()

        logger.warning(
            "Could not update missing sale ID %s",
            sale_id
        )

        return jsonify({
            "error": "Sale not found"
        }), 404

    connection.execute("""
        UPDATE sales
        SET product = ?, price = ?, quantity = ?
        WHERE id = ?
    """, (
        product,
        price,
        quantity,
        sale_id
    ))

    connection.commit()
    connection.close()

    logger.info(
        "Updated sale ID %s",
        sale_id
    )

    return jsonify({
        "message": "Sale updated successfully"
    })


@app.route("/sales/<int:sale_id>", methods=["DELETE"])
def delete_sale(sale_id):
    connection = get_database()

    sale = connection.execute(
        "SELECT * FROM sales WHERE id = ?",
        (sale_id,)
    ).fetchone()

    if sale is None:
        connection.close()

        logger.warning(
            "Could not delete missing sale ID %s",
            sale_id
        )

        return jsonify({
            "error": "Sale not found"
        }), 404

    connection.execute(
        "DELETE FROM sales WHERE id = ?",
        (sale_id,)
    )

    connection.commit()
    connection.close()

    logger.info(
        "Deleted sale ID %s",
        sale_id
    )

    return jsonify({
        "message": "Sale deleted successfully"
    })


@app.route("/analytics", methods=["GET"])
def analytics():
    tracemalloc.start()

    def run_query(query):
        connection = get_database()
        result = connection.execute(query).fetchone()[0]
        connection.close()

        if result is None:
            return 0

        return result

    with ThreadPoolExecutor(max_workers=3) as executor:
        revenue_task = executor.submit(
            run_query,
            "SELECT SUM(price * quantity) FROM sales"
        )

        items_task = executor.submit(
            run_query,
            "SELECT SUM(quantity) FROM sales"
        )

        products_task = executor.submit(
            run_query,
            "SELECT COUNT(DISTINCT product) FROM sales"
        )

        total_revenue = revenue_task.result()
        total_items = items_task.result()
        number_of_products = products_task.result()

    current_memory, peak_memory = (
        tracemalloc.get_traced_memory()
    )

    tracemalloc.stop()

    current_kb = current_memory / 1024
    peak_kb = peak_memory / 1024

    logger.info(
        "Analytics completed concurrently"
    )

    logger.info(
        "Memory usage: current %.2f KB, peak %.2f KB",
        current_kb,
        peak_kb
    )

    return jsonify({
        "total_revenue": total_revenue,
        "total_items_sold": total_items,
        "number_of_products": number_of_products,
        "current_memory_kb": round(current_kb, 2),
        "peak_memory_kb": round(peak_kb, 2)
    })


@app.route("/upload", methods=["POST"])
def upload_sales():
    if "file" not in request.files:
        logger.warning(
            "CSV upload request contained no file"
        )

        return jsonify({
            "error": "No CSV file was provided"
        }), 400

    uploaded_file = request.files["file"]

    if uploaded_file.filename == "":
        logger.warning(
            "CSV upload request had an empty filename"
        )

        return jsonify({
            "error": "No file was selected"
        }), 400

    try:
        sales_data = pd.read_csv(uploaded_file)

        required_columns = [
            "product",
            "price",
            "quantity"
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in sales_data.columns
        ]

        if missing_columns:
            logger.warning(
                "CSV was missing columns: %s",
                missing_columns
            )

            return jsonify({
                "error": "Missing columns",
                "columns": missing_columns
            }), 400

        sales_data = sales_data[required_columns]
        sales_data = sales_data.dropna()

        sales_data["price"] = pd.to_numeric(
            sales_data["price"],
            errors="coerce"
        )

        sales_data["quantity"] = pd.to_numeric(
            sales_data["quantity"],
            errors="coerce"
        )

        sales_data = sales_data.dropna()

        sales_data = sales_data[
            (sales_data["price"] >= 0)
            & (sales_data["quantity"] > 0)
        ]

        records = [
            (
                row["product"],
                float(row["price"]),
                int(row["quantity"])
            )
            for _, row in sales_data.iterrows()
        ]

        connection = get_database()

        connection.executemany("""
            INSERT INTO sales (product, price, quantity)
            VALUES (?, ?, ?)
        """, records)

        connection.commit()
        connection.close()

        logger.info(
            "Imported %s records from CSV file %s",
            len(records),
            uploaded_file.filename
        )

        return jsonify({
            "message": "CSV imported successfully",
            "records_added": len(records)
        }), 201

    except Exception as error:
        logger.exception(
            "CSV upload failed"
        )

        return jsonify({
            "error": str(error)
        }), 500


if __name__ == "__main__":
    logger.info("Application started")
    create_database()
    logger.info("Database initialized")
    app.run(debug=True)
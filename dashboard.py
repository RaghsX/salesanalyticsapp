import streamlit as st
import requests
import pandas as pd

API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:5000"
)

st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("Sales Analytics Dashboard")

uploaded_file = st.file_uploader(
    "Upload a sales CSV file",
    type=["csv"]
)

try:
    # Load uploaded CSV or get data from Flask
    if uploaded_file is not None:
        sales_table = pd.read_csv(uploaded_file)
        st.success("CSV loaded successfully!")

        if st.button("Save CSV to Database"):
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "text/csv"
                )
            }

            upload_response = requests.post(
                f"{API_URL}/upload",
                files=files,
                timeout=10
            )

            if upload_response.status_code == 201:
                result = upload_response.json()

                st.success(
                    f"{result['records_added']} records "
                    "saved to the database!"
                )

            else:
                st.error("Could not save the CSV.")

    else:
        response = requests.get(
            f"{API_URL}/sales",
            timeout=5
        )

        response.raise_for_status()
        sales_table = pd.DataFrame(response.json())
        st.success("Connected to the Flask API!")

    required_columns = [
        "product",
        "price",
        "quantity"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in sales_table.columns
    ]

    if missing_columns:
        st.error(
            "Missing columns: "
            + ", ".join(missing_columns)
        )

    elif sales_table.empty:
        st.warning("There are currently no sales records.")

    else:
        # Calculate revenue
        sales_table["revenue"] = (
            sales_table["price"]
            * sales_table["quantity"]
        )

        total_revenue = sales_table["revenue"].sum()
        total_items = sales_table["quantity"].sum()
        number_of_products = sales_table["product"].nunique()

        # Summary metrics
        st.subheader("Sales Summary")

        column1, column2, column3 = st.columns(3)

        column1.metric(
            "Total Revenue",
            f"${total_revenue:,.2f}"
        )

        column2.metric(
            "Items Sold",
            int(total_items)
        )

        column3.metric(
            "Products",
            number_of_products
        )

        # Add sale
        st.subheader("Add a New Sale")

        with st.form("new_sale_form"):
            new_product = st.text_input("Product name")

            new_price = st.number_input(
                "Price",
                min_value=0.01,
                step=1.00
            )

            new_quantity = st.number_input(
                "Quantity",
                min_value=1,
                step=1
            )

            submit_sale = st.form_submit_button(
                "Add Sale"
            )

        if submit_sale:
            if not new_product.strip():
                st.error("Please enter a product name.")

            else:
                new_sale = {
                    "product": new_product.strip(),
                    "price": float(new_price),
                    "quantity": int(new_quantity)
                }

                add_response = requests.post(
                    f"{API_URL}/sales",
                    json=new_sale,
                    timeout=5
                )

                if add_response.status_code == 201:
                    st.success(
                        "Sale added successfully!"
                    )
                    st.rerun()

                else:
                    st.error(
                        "Could not add the sale."
                    )

        # Update and delete require database IDs
        if "id" in sales_table.columns:
            # Update sale
            st.subheader("Update a Sale")

            update_id = st.selectbox(
                "Choose the sale ID to update",
                sales_table["id"].tolist(),
                key="update_id"
            )

            selected_sale = sales_table[
                sales_table["id"] == update_id
            ].iloc[0]

            with st.form("update_sale_form"):
                updated_product = st.text_input(
                    "Updated product name",
                    value=str(selected_sale["product"])
                )

                updated_price = st.number_input(
                    "Updated price",
                    min_value=0.01,
                    value=float(selected_sale["price"]),
                    step=1.00
                )

                updated_quantity = st.number_input(
                    "Updated quantity",
                    min_value=1,
                    value=int(selected_sale["quantity"]),
                    step=1
                )

                submit_update = st.form_submit_button(
                    "Update Sale"
                )

            if submit_update:
                if not updated_product.strip():
                    st.error(
                        "Please enter a product name."
                    )

                else:
                    updated_data = {
                        "product": updated_product.strip(),
                        "price": float(updated_price),
                        "quantity": int(updated_quantity)
                    }

                    update_response = requests.put(
                        f"{API_URL}/sales/{update_id}",
                        json=updated_data,
                        timeout=5
                    )

                    if update_response.status_code == 200:
                        st.success(
                            "Sale updated successfully!"
                        )
                        st.rerun()

                    else:
                        st.error(
                            "Could not update the sale."
                        )

            # Delete sale
            st.subheader("Delete a Sale")

            delete_id = st.selectbox(
                "Choose the sale ID to delete",
                sales_table["id"].tolist(),
                key="delete_id"
            )

            delete_sale = st.button(
                "Delete Selected Sale"
            )

            if delete_sale:
                delete_response = requests.delete(
                    f"{API_URL}/sales/{delete_id}",
                    timeout=5
                )

                if delete_response.status_code == 200:
                    st.success(
                        "Sale deleted successfully!"
                    )
                    st.rerun()

                else:
                    st.error(
                        "Could not delete the sale."
                    )

        # Product filter
        st.subheader("Filter Sales")

        product_choices = (
            ["All"]
            + sales_table["product"].unique().tolist()
        )

        selected_product = st.selectbox(
            "Choose a product",
            product_choices
        )

        if selected_product == "All":
            filtered_table = sales_table
        else:
            filtered_table = sales_table[
                sales_table["product"]
                == selected_product
            ]

        # Sales table
        st.subheader("Sales Records")

        st.dataframe(
            filtered_table,
            use_container_width=True
        )

        # Download button
        csv_data = filtered_table.to_csv(
            index=False
        )

        st.download_button(
            label="Download Sales Data",
            data=csv_data,
            file_name="processed_sales.csv",
            mime="text/csv"
        )

        # Revenue chart
        st.subheader("Revenue by Product")

        chart_data = filtered_table.set_index(
            "product"
        )["revenue"]

        st.bar_chart(chart_data)

except requests.exceptions.ConnectionError:
    st.error(
        "Could not connect to Flask. "
        "Make sure app.py is running."
    )

except requests.exceptions.RequestException as error:
    st.error(f"API error: {error}")

except Exception as error:
    st.error(f"Something went wrong: {error}")

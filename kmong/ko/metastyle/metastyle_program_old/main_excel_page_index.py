import pandas as pd
from openpyxl import Workbook

def process_excel():
    # Read the Excel file
    input_file = 'metastyle_20250117235442.xlsx'
    output_file = 'output.xlsx'

    # Load data into a DataFrame
    df = pd.read_excel(input_file)

    # Add page and page_index columns
    df['page'] = 0
    df['page_index'] = 0

    # Initialize variables
    current_page = 5
    current_index = 0
    previous_product_name = None

    # Iterate through rows to assign page and page_index
    for i, row in df.iterrows():
        if row['product_name'] != previous_product_name:
            current_index += 1
            if current_index > 60:
                current_page += 1
                current_index = 1

        df.at[i, 'page'] = current_page
        df.at[i, 'page_index'] = current_index

        # Update previous_product_name
        previous_product_name = row['product_name']

    # Save the resulting DataFrame to a new Excel file
    df.to_excel(output_file, index=False)
    print(f"Processed data saved to {output_file}")

# Run the function
process_excel()

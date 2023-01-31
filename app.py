import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

file_path = filedialog.askopenfilename()

print('Choose flat file disbursement report from Amazon (.txt)')
data = pd.read_table(file_path)
# data = pd.read_table('64651019375 (1).txt')
item_ids = pd.read_csv('item_ids.csv')

# statement level info is on first line of data. Copy it for verification at the end then drop from df
statement_row = data.iloc[0,:]
statement_row['deposit-date'] = pd.to_datetime(statement_row['deposit-date'])
data.iloc[0,:].drop

# merge with Item IDs lookup table to get item id from sku
data = data.merge(item_ids, on='sku', how='left')


# sort amount description values into category lists
amount_description_list = data['amount-description'].unique().astype('str')

invoice_descriptions = []
fee_descriptions = []
reserve_descriptions = []

for item in amount_description_list:

    if item.isupper() == True:
        # print(item, '....invoice')
        invoice_descriptions.append(item)

    elif "Reserve" in item:
        # print(item, '....reserve')
        reserve_descriptions.append(item)

    elif item == "Principal":
        # print(item, '....invoice')
        invoice_descriptions.append(item)

    else:
        # print(item, '....fee')
        fee_descriptions.append(item)

# sum amounts for fee type amount descriptions
fees_data = data[data['amount-description'].isin(fee_descriptions)]
fees_pivot = pd.pivot_table(fees_data, index='amount-description', values='amount', aggfunc=np.sum, margins=True)

# sum amounts for reserve type amount descriptions
reserve_data = data[data['amount-description'].isin(reserve_descriptions)]
reserve_pivot = pd.pivot_table(reserve_data, index='amount-description', values='amount', aggfunc=np.sum, margins=True)

# sum qty and amount by item ID for invoice type amount descriptions
invoice_data = data[data['amount-description'].isin(invoice_descriptions)]
invoice_pivot = pd.pivot_table(invoice_data, index='Item ID', values=['quantity-purchased','amount'], aggfunc=np.sum, margins=True)

# make csv for importing into sage
import_df = pd.DataFrame(columns=['Customer ID', 'Invoice/CM #', 'Date', 'Customer PO', 'Date Due', 'Sales Representative ID', 'Accounts Receivable Account', 'Number of Distributions', 'Quantity', 'Item ID', 'Serial Number', 'G/L Acount', 'Tax Type', 'Amount', 'Sales Tax Agency ID', 'Voided by Transaction', 'Recur Number', 'Recur Frequency'])
invoice_num = 'A' + statement_row['deposit-date'].strftime("%y%m%d")
po_num = 'ID ' + str(statement_row['settlement-id'])
invoice_date = statement_row['deposit-date'].strftime("%m/%d/%y")

for index, row in invoice_pivot.iterrows():
    new_row = pd.DataFrame([{
            'Customer ID':'AMAZ00',
            'Invoice/CM #':invoice_num,
            'Date':invoice_date,
            'Customer PO':po_num,
            'Date Due':invoice_date,
            'Sales Representative ID':'ZZRETA',
            'Accounts Receivable Account':'12100',
            'Number of Distributions':len(invoice_pivot)-1,
            'Quantity':row['quantity-purchased'],
            'Item ID':index,
            'Serial Number':'',
            'G/L Acount':'30100',
            'Tax Type':'1',
            'Amount':round(-1 * row['amount'], 2),
            'Sales Tax Agency ID':'',
            'Voided by Transaction':'',
            'Recur Number':'0',
            'Recur Frequency':'0'
    }])

    import_df = pd.concat([import_df, new_row])


invoice_total = import_df[import_df['Item ID']=='All']['Amount'].values

import_df = import_df[import_df['Item ID'] != 'All']

print('Choose file path to save import template csv to.')
file_path = filedialog.asksaveasfile(initialfile = 'Untitled.csv', defaultextension=".csv")
import_df.to_csv(file_path, index=False)